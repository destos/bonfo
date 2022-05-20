"""Board package for Bonfo."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import AsyncIterator, Coroutine, Iterable, Optional

from construct import ConstError, StreamError
from semver import VersionInfo
from serial_asyncio import open_serial_connection, serial

from bonfo.exceptions import BonfoOperatorException

from .msp.codes import MSP
from .msp.fields.base import Direction
from .msp.fields.pids import MSPFields
from .msp.fields.statuses import ApiVersion, BoardInfo, BuildInfo, CombinedBoardInfo, FcVariant, FcVersion, Name, Uid
from .msp.message import Data, Preamble
from .msp.utils import msg_data, out_message_builder
from .profile import Profile

logger = logging.getLogger(__name__)


__all__ = ["Board"]


@dataclass
class Board:
    """Board is an interface for , configuration retrieval and saving."""

    device: str
    baudrate: int = 115200
    initial_data: bool = True
    loop: Optional[asyncio.AbstractEventLoop] = None
    profile: Optional[Profile] = None

    _ready_tasks: Iterable[Coroutine] = field(default_factory=lambda: list(), init=False, repr=False)

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
        if self.initial_data:
            self._ready_task(self.get_board_info())
        self.loop.create_task(self._run_ready_tasks())

    def _ready_task(self, coro: Coroutine) -> None:
        self._ready_tasks.append(coro)  # type:ignore

    async def _run_ready_tasks(self) -> None:
        await asyncio.gather(*self._ready_tasks)
        self.ready.set()

    async def get_board_info(self) -> CombinedBoardInfo:
        await self.connected.wait()
        name = await (self > Name)
        api = await (self > ApiVersion)
        version = await (self > FcVersion)
        build_info = await (self > BuildInfo)
        board_info = await (self > BoardInfo)
        variant = await (self > FcVariant)
        uid = await (self > Uid)
        self.info = CombinedBoardInfo(
            name,
            api,
            version,
            build_info,
            board_info,
            variant,
            uid,
        )
        return self.info

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
        # self.loop.close()

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

            try:
                preamble = Preamble.parse(preamble_bytes)
            except (StreamError, ConstError) as e:
                logger.exception("Error with preamble bytes", exc_info=e)
                return None, None
            logger.debug(
                "received: preamble code %s (%s): %s", MSP(preamble.frame_id), preamble.data_length, preamble_bytes
            )
            if preamble.data_length > 0:
                total_length = preamble.data_length + 1
                data_bytes = await self.reader.read(total_length)
                all_bytes = preamble_bytes + data_bytes
                data_bytes = preamble_bytes[3:5] + data_bytes
                logger.debug("all bytes: %s", all_bytes)
                msp = self.msp_version
                msg = Data.parse(data_bytes, msp=msp)
                data = msg_data(msg)
                logger.debug("msp: %s fields: %s", msp, data)
                return preamble, data
            else:
                # read last crc byte
                # TODO: fix message struct as to actually perform crc when receiving messages
                await self.reader.read(1)

            return preamble, None

    async def send_receive(self, code: MSP, fields):
        # TODO: Use an asyncio Queue to make sure the send/receive happens consecutively?
        async with self.message_lock:
            await self.send_msg(code, fields=fields)
            return await self.receive_msg()

    async def get(self, fields):
        """Get data from the board with optional fields values.

        Args:
            fields (Fields): The un-initialized or MSPFields instance with values.

        Returns:
            DataclassStruct: The data class instance related to the get request
        """
        assert fields.get_direction() in [Direction.OUT, Direction.BOTH]
        assert fields.get_code is not None

        async with self.message_lock:
            await self.send_msg(fields.get_code)
            pre, data = await self.receive_msg()
            if pre is None:
                return None
            # assert code received is the same get_code
            assert fields.get_code == pre.frame_id
            # TODO: raise error if preamble received is an error
            return data

    async def set(self, fields):
        """Sends a set message to the board with the values of the given fields.

        Args:
            fields (Fields): The un-initialized or MSPFields instance with values.

        Returns:
            DataclassStruct: The data class instance related to the set request
        """
        assert fields.get_direction() in [Direction.IN, Direction.BOTH]
        assert fields.set_code is not None

        async with self.message_lock:
            await self.send_msg(fields.set_code, fields=fields)
            pre, data = await self.receive_msg()
            if pre is None:
                return None
            # assert code received is the same set_code
            assert fields.set_code == pre.frame_id
            # TODO: raise error if preamble received is an error
            return data

    async def __gt__(self, other):
        """Get data from the board with the > operator."""
        if isinstance(other, MSPFields) or issubclass(other, MSPFields):
            return await self.get(other)
        raise BonfoOperatorException("Not a compatible > type")

    async def __lt__(self, other):
        """Set data on the board with the < operator."""
        if isinstance(other, MSPFields) or issubclass(other, MSPFields):
            return await self.set(other)
        raise BonfoOperatorException("Not a compatible < type")
