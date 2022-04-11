"""Board package for Bonfo."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Tuple, Union

from construct import Container
from serial_asyncio import open_serial_connection, serial

from .msp.codes import MSP
from .msp.message import Data, Preamble
from .msp.state import Config, RcTuning, RxConfig
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
    # pid: Annotated[int, field(default=1)]
    # rate: Annotated[int, field(default=1)]

    # pid: int
    # rate: int
    _pid = 0
    _rate = 0

    # Track profile changes before they are applied
    _profile_tracker = (0, 0)

    # hold previous profiles for reversion purposes
    _revert_to_profiles = (0, 0)

    class SyncedState(Enum):
        """Local synced/saved status for selected profiles."""

        UNFETCHED = 1
        CLEAN = 2
        AWAITING_APPLY = 3

    _state = SyncedState.UNFETCHED

    def __str__(self) -> str:
        return f"pid: {self.pid} rate: {self.rate} {self._state}"

    @property
    def pid(self) -> int:
        return self._pid

    @pid.setter
    def pid(self, pid: Union[int, None]) -> None:
        if pid is None:
            return
        assert pid in range(1, 4), "PID out of range"
        self._profile_tracker = (pid, self._profile_tracker[1])
        self._state = self.SyncedState.AWAITING_APPLY

    @property
    def rate(self) -> int:
        return self._rate

    @rate.setter
    def rate(self, rate: Union[int, None]) -> None:
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
    async def __call__(self, pid: Union[int, None] = None, rate: Union[int, None] = None, revert_on_exit=False):
        # wait here till the board is ready
        await self.board.ready.wait()

        logger.debug("Asked to set profiles to: %s", (pid, rate))
        logger.debug("Got current profiles from Board: %s", self._profile_tracker)

        self._revert_to_profiles = (self.pid, self.rate)
        logger.debug("Setting _revert_to_profiles to: %s", self._revert_to_profiles)

        (self.pid, self.rate) = (pid, rate)

        await self.apply_changes()

        logger.debug("returning profile context")

        yield self
        if revert_on_exit:
            logger.debug("reverting profiles")
            (self.pid, self.rate) = self._revert_to_profiles
            await self.apply_changes()

    async def _set_profiles_from_board(self) -> Tuple[int, int]:
        p, status = await self.board.send_receive(MSP.STATUS_EX)
        self._state = self.SyncedState.CLEAN
        self._profile_tracker = (self._pid, self._rate) = (status.pid_profile, status.rate_profile)
        return self._profile_tracker

    async def _set_pid_to_board(self, pid) -> bool:
        logger.debug("PID profile to: %s", pid)
        p, msg = await self.board.send_receive(MSP.SELECT_SETTING, dict(pid_profile=pid))

    async def _set_rate_to_board(self, rate) -> bool:
        logger.debug("Rate profile to: %s", rate)
        p, msg = await self.board.send_receive(MSP.SELECT_SETTING, dict(rate_profile=rate))

    async def apply_changes(self):
        """Apply any locally changed profiles to the board."""
        assert self._state == self.SyncedState.AWAITING_APPLY
        (asked_pid, asked_rate) = self._profile_tracker
        if asked_pid != self.pid:
            logger.debug("PID profile differs, updating board")
            await self._set_pid_to_board(asked_pid)
        if asked_rate != self.rate:
            logger.debug("Rate profile differs, updating board")
            await self._set_rate_to_board(asked_rate)

        (found_pid, found_rate) = await self._set_profiles_from_board()
        # Sanity assertions
        assert asked_pid == found_pid
        assert asked_rate == found_rate


class Board:
    """Board is an interface for serial connection, configuration retrieval and saving."""

    _ready_tasks = []

    # TODO: allow to pass init profiles to Profile from board init
    def __init__(self, device: str, baudrate: int = 115200, trials=100) -> None:
        # events
        self.connected = asyncio.Event()
        self.ready = asyncio.Event()

        self.read_lock = asyncio.Lock()
        self.write_lock = asyncio.Lock()

        self.device = device
        self.baudrate = baudrate

        loop = asyncio.get_running_loop()

        # found board configuration
        self.conf = Config()
        # rate and pid profile manager
        self.profile = Profile(board=self)
        self._ready_task(self.profile._check_connection)

        # TODO: register configs for saving/applying?
        self.rx_conf = RxConfig()
        self.rc_tuning = RcTuning()

        # Serial options/state
        self.serial_trials = trials
        self._ready_task(self.open_serial)
        loop.create_task(self._run_ready_tasks())

    def _ready_task(self, coro):
        self._ready_tasks.append(coro())

    async def _run_ready_tasks(self):
        await asyncio.gather(*self._ready_tasks)
        self.ready.set()

    async def open_serial(self, baudrate: Union[int, None] = None, **kwargs):
        baudrate = baudrate or self.baudrate
        try:
            self.reader, self.writer = await open_serial_connection(
                url=self.device,
                baudrate=baudrate,
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
    async def connect(self):
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

    async def send_msg(self, code: MSP, data=None, blocking=True, timeout=-1):
        """Generates and sends a message with the passed code and data.

        Args:
            code (MSP): MSP code enum or code integer
            data (Any supported message struct, optional): structured data to send,
                converted to binary by struct. Defaults to None.

        Returns:
            int: Total bytes sent
        """
        buff = out_message_builder(code, fields=data)

        async with self.write_lock:
            try:
                self.writer.write(buff)
            except serial.SerialException as e:
                logger.exception("Error writing to serial port", exc_info=e)
            finally:
                logger.debug("sent: %s %s", code, buff)

    async def send_receive(self, code: MSP, data=None) -> Union[None, Container]:
        # Use an asyncio Queue to make sure the send/receive happens consecutively.
        await self.send_msg(code, data=data)
        return await self.receive_msg()

    async def receive_msg(self):
        """Read the current line from the serial port and parse the MSP message.

        Parse the message and return a contstruct Container.

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
                msg = Data.parse(data_bytes)
                logger.debug("all bytes: %s", all_bytes)
                return preamble, msg_data(msg)
            else:
                # read last crc byte
                await self.reader.read(1)

            return preamble, None

