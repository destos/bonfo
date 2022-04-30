"""Board package for Bonfo."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncIterator, Coroutine, List, Optional, Tuple, Type, Union

from construct import Container
from semver import VersionInfo
from serial_asyncio import open_serial_connection, serial

from .msp.codes import MSP
from .msp.fields.base import Direction
from .msp.fields.config import SelectPID, SelectRate
from .msp.fields.pids import MSPFields
from .msp.fields.statuses import (
    ApiVersion,
    BoardInfo,
    BuildInfo,
    CombinedBoardInfo,
    FcVariant,
    FcVersion,
    Name,
    StatusEx,
    Uid,
)
from .msp.message import Data, Preamble
from .msp.utils import msg_data, out_message_builder

logger = logging.getLogger(__name__)


__all__ = ["Board", "Profile"]


@dataclass
class Profile:
    """Profile context manager.

    pid and rate properties should always reflect what is currently selected on the board.

    When dealing with internal profile tuples, the order will always be (pid, rate).
    """

    board: "Board"
    # pid: int = 1
    # rate: int = 1
    # pid: Annotated[int, field(default=1)]
    # rate: Annotated[int, field(default=1)]

    # pid: int
    # rate: int
    # TODO: move to property classes that have individual synced states and setters
    _pid: int = field(default=1, init=False, repr=False)
    _rate: int = field(default=1, init=False, repr=False)

    # Track profile changes before they are applied
    _profile_tracker: Tuple[int, int] = field(default_factory=lambda: (1, 1), repr=False)

    # hold previous profiles for reversion purposes
    _revert_to_profiles: Tuple[int, int] = field(default_factory=lambda: (1, 1), repr=False)

    class SyncedState(Enum):
        """Local synced/saved status for selected profiles."""

        UNFETCHED = 1
        FETCHING = 2
        CLEAN = 3
        AWAITING_APPLY = 4

    _state = SyncedState.UNFETCHED

    def __str__(self) -> str:
        return f"pid: {self.pid} rate: {self.rate} {self._state}"

    @property
    def pid(self) -> int:
        if self._state == self.SyncedState.UNFETCHED:
            logger.warning("PID profile not yet fetched from board")
        return self._pid

    @pid.setter
    def pid(self, pid: Optional[int]) -> None:
        if pid is None:
            return
        assert pid in range(1, 4), "PID out of range"
        self._profile_tracker = (pid, self._profile_tracker[1])
        self._state = self.SyncedState.AWAITING_APPLY

    @property
    def rate(self) -> int:
        if self._state == self.SyncedState.UNFETCHED:
            logger.warning("Rate profile not yet fetched from board")
        return self._rate

    @rate.setter
    def rate(self, rate: Optional[int]) -> None:
        if rate is None:
            return
        assert rate in range(1, 7), "Rate out of range"
        self._profile_tracker = (self._profile_tracker[0], rate)
        self._state = self.SyncedState.AWAITING_APPLY

    async def _check_connection(self):
        """Wait for a connection, then get current profiles from board."""
        await self.board.connected.wait()
        await self._set_profiles_from_board()

    @asynccontextmanager
    async def __call__(
        self, pid: Optional[int] = None, rate: Optional[int] = None, revert_on_exit=False
    ) -> AsyncIterator["Profile"]:
        self._state = self.SyncedState.FETCHING

        # wait here till the board is ready
        await self.board.ready.wait()

        logger.debug("Asked to set profiles to: %s", (pid, rate))
        logger.debug("Got current profiles from Board: %s", self._profile_tracker)

        self._revert_to_profiles = (self.pid, self.rate)
        logger.debug("Setting _revert_to_profiles to: %s", self._revert_to_profiles)

        (self.pid, self.rate) = (pid, rate)  # type:ignore

        await self.apply_changes()

        logger.debug("returning profile context")

        yield self
        if revert_on_exit:
            logger.debug("reverting profiles")
            (self.pid, self.rate) = self._revert_to_profiles
            await self.apply_changes()

    async def _set_profiles_from_board(self) -> Tuple[int, int]:
        _, status = await self.board.get(StatusEx)
        if status is None:
            return self._profile_tracker
        self._state = self.SyncedState.CLEAN
        self._profile_tracker = (self._pid, self._rate) = (status.pid_profile, status.rate_profile)
        return self._profile_tracker

    async def _send_pid_to_board(self, pid) -> bool:
        logger.debug("PID profile to: %s", pid)
        p, _ = await self.board.set(SelectPID(pid))
        # return p.message_type != "ERR"
        return True

    async def _send_rate_to_board(self, rate) -> bool:
        logger.debug("Rate profile to: %s", rate)
        p, _ = await self.board.set(SelectRate(rate))
        return True

    async def apply_changes(self) -> bool:
        """Apply any locally changed profiles to the board.

        Returns False if it failed to apply.
        """
        if not self._state == self.SyncedState.AWAITING_APPLY:
            return False
        (asked_pid, asked_rate) = self._profile_tracker
        if asked_pid != self.pid:
            logger.debug("PID profile differs, updating board")
            await self._send_pid_to_board(asked_pid)
        if asked_rate != self.rate:
            logger.debug("Rate profile differs, updating board")
            await self._send_rate_to_board(asked_rate)

        (found_pid, found_rate) = await self._set_profiles_from_board()
        # Sanity check
        if asked_pid != found_pid or asked_rate != found_rate:
            return False
        return True


@dataclass
class Board:
    """Board is an interface for serial connection, configuration retrieval and saving."""

    device: str
    baudrate: int = 115200
    serial_trails: int = 100
    loop: Optional[asyncio.AbstractEventLoop] = None
    profile: Optional[Profile] = None

    _ready_tasks: List[Coroutine] = field(default_factory=lambda: list(), init=False, repr=False)

    # TODO: allow to pass init profiles to Profile from board init
    def __post_init__(self) -> None:
        # board events
        self.connected = asyncio.Event()
        self.ready = asyncio.Event()

        self.read_lock = asyncio.Lock()
        self.write_lock = asyncio.Lock()
        self.message_lock = asyncio.Lock()

        if self.loop is None:
            self.loop = asyncio.get_running_loop()

        # TODO: every message sent by the board attaches the current msp version to the context
        # for conditional struct building. The initial board message can't send it as
        self.info = CombinedBoardInfo(None, None, None, None, None, None, None)

        # rate and pid profile manager
        # TODO: handle assigning board to custom profiles
        if self.profile is None:
            self.profile = Profile(board=self)
        self._ready_task(self.profile._check_connection())

        # TODO: register configs for saving/applying?
        # self.rx_conf = RxConfig()
        # self.rc_tuning = RcTuning()

        self._ready_task(self.open_serial())
        self._ready_task(self.get_board_info())
        self.loop.create_task(self._run_ready_tasks())

    def _ready_task(self, coro: Coroutine) -> None:
        self._ready_tasks.append(coro)

    async def _run_ready_tasks(self) -> None:
        await asyncio.gather(*self._ready_tasks)
        self.ready.set()

    async def get_board_info(self) -> None:
        await self.connected.wait()
        _, name = await self.get(Name)
        _, api = await self.get(ApiVersion)
        _, version = await self.get(FcVersion)
        _, build_info = await self.get(BuildInfo)
        _, board_info = await self.get(BoardInfo)
        _, variant = await self.get(FcVariant)
        _, uid = await self.get(Uid)
        self.info = CombinedBoardInfo(
            name,
            api,
            version,
            build_info,
            board_info,
            variant,
            uid,
        )

    @property
    def msp_version(self) -> Optional[VersionInfo]:
        try:
            return self.info.api.semver  # type:ignore
        except AttributeError:
            return None

    async def open_serial(self, **kwargs) -> None:
        try:
            self.reader, self.writer = await open_serial_connection(
                url=self.device,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False,
                # writeTimeout=0,
                **kwargs,
            )
            self.connected.set()
        except serial.SerialException as exc:
            logger.exception("Unable to connect to the serial device %s: Will retry", self.device, exc_info=exc)
        logger.info("connected to serial device %s", self.device)

    @asynccontextmanager
    async def connect(self) -> AsyncIterator["Board"]:
        try:
            await self.ready.wait()
            yield self
        except Exception as e:
            logger.exception("Error during connection to board", exc_info=e)
        finally:
            self.disconnect()

    def disconnect(self):
        self.connected.clear()
        # self.loop_task.cancel()

    # TODO: update fields arg requirement here
    async def send_msg(self, code: MSP, fields=None, blocking=True, timeout=-1):
        """Generates and sends a message with the passed code and data.

        Args:
            code (MSP): MSP code enum or code integer
            fields (Any supported message struct, optional): structured data to send,
                converted to binary by struct. Defaults to None.

        Returns:
            int: Total bytes sent
        """
        buff = out_message_builder(code, fields=fields, msp=self.msp_version)

        async with self.write_lock:
            try:
                self.writer.write(buff)
            except serial.SerialException as e:
                logger.exception("Error writing to serial port", exc_info=e)
            finally:
                logger.debug("sent: %s %s", code, buff)

    async def receive_msg(self):
        """Read the current line from the serial port and parse the MSP message.

        Parse the message and return a construct Container.

        Returns:
            Container | None: Containter holding the message data, or None on no data.
        """
        # "All this because reader.readline wasn't working... :/"
        async with self.read_lock:
            preamble_bytes = await self.reader.read(5)

            preamble = Preamble.parse(preamble_bytes)
            logger.debug(
                "received: preamble code %s (%s): %s", MSP(preamble.frame_id), preamble.data_length, preamble_bytes
            )
            if preamble.data_length > 0:
                total_length = preamble.data_length + 1
                data_bytes = await self.reader.read(total_length)
                all_bytes = preamble_bytes + data_bytes
                data_bytes = preamble_bytes[3:5] + data_bytes
                logger.debug("all bytes: %s", all_bytes)
                msg = Data.parse(data_bytes, msp=self.msp_version)
                data = msg_data(msg)
                logger.debug("fields: %s", data)
                return preamble, data
            else:
                # read last crc byte
                # TODO: fix message struct as to actually perform crc when receiving messages
                await self.reader.read(1)

            return preamble, None

    async def send_receive(self, code: MSP, fields=None) -> Union[None, Container]:
        # TODO: Use an asyncio Queue to make sure the send/receive happens consecutively?
        async with self.message_lock:
            await self.send_msg(code, fields=fields)
            return await self.receive_msg()

    async def get(self, fields: Type[MSPFields]):
        assert fields.get_direction() in [Direction.OUT, Direction.BOTH]
        assert fields.get_code is not None

        async with self.message_lock:
            await self.send_msg(fields.get_code)
            # TODO: assert code received is the same get_code
            return await self.receive_msg()

    async def set(self, fields: Type[MSPFields]):
        assert fields.get_direction() in [Direction.IN, Direction.BOTH]
        assert fields.set_code is not None

        async with self.message_lock:
            await self.send_msg(fields.set_code, fields=fields)
            # TODO: assert code received is the same get_code
            return await self.receive_msg()

    async def __add__(self, other):
        if issubclass(other, MSPFields):
            return await self.set(other)

    async def __sub__(self, other):
        if issubclass(other, MSPFields):
            return await self.get(other)
