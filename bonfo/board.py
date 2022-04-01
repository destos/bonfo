"""Board package for Bonfo."""
import logging
import time
from dataclasses import dataclass, field
from multiprocessing import BoundedSemaphore
from typing import Sequence

import serial

from .msp.codes import MSP
from .msp.message import Message
from .msp.state import Config, RcTuning, RxConfig
from .msp.utils import out_message_builder

logger = logging.getLogger(__name__)


class Board:
    """Board is an interface for the serial connection, configuration retrieval and saving of data."""

    @dataclass
    class Profile:
        """Profile context manager"""

        board: "Board" = None
        profile: int = 0
        profiles: Sequence[int] = field(default_factory=set)

        def __post_init__(self, *args, **kwargs):
            pass
            # super().__post_init__(self, *args, **kwargs)

        def __enter__(self, profile_id: int = 0):
            pass

        def __exit__(self, exc_type, exc_value, traceback):
            pass

    def __init__(self, port: str, baudrate: int = 115200, trials=100) -> None:
        self.conf = Config()
        self.profile = self.Profile(board=self)

        # TODO: register configs for saving/applying?
        self.rx_conf = RxConfig()
        self.rc_tuning = RcTuning()

        # Serial options/state
        self.serial_trials = trials
        self.serial_write_lock = BoundedSemaphore(value=1)
        self.serial_read_lock = BoundedSemaphore(value=1)
        self.is_serial_open = False
        self.serial = self._init_serial(port, baudrate=baudrate)

    def _init_serial(self, port: str, baudrate: int = 115200):
        serial_port = serial.Serial(
            port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.1,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
            writeTimeout=0,
        )
        logger.info("New serial port initialized:", serial_port)
        return serial_port

    def __enter__(self):
        if self.connect(trials=self.serial_trials):
            return self
        else:
            logger.warning("Serial port ({}) not ready/available".format(self.serial.port))
            return False

    def __exit__(self, exc_type, exc_value, traceback):
        if self.serial.is_open:
            self.serial.readlines
            self.serial.close()

    def connect(self, trials=100, delay=0.5):
        """Opens the serial connection with the board.

        Args:
            trials (int, optional): How many times to try and connect. Defaults to 100.
            delay (float, optional): Wait between connection trials. Defaults to 0.5.

        Returns:
            bool: True on a successful connection
        """
        for _ in range(trials):
            try:
                if self.serial.is_open:
                    self.serial.close()
                self.serial.open()
                # self.basic_info()
                return True

            except serial.SerialException as err:
                logger.warning("Error opening the serial port ({0}): {1}".format(self.serial.port, err), exc_info=err)

            except FileNotFoundError as err:
                logger.warning("Port ({0}) not found: {1}".format(self.serial.port, err), exc_info=err)
            time.sleep(delay)

        return False

    def send_msg(self, code: MSP, data=None, blocking=True, timeout=-1):
        """Generates and sends a message with the passed code and data.

        Args:
            code (MSP): MSP code enum or code integer
            data (Any supported message struct, optional): structured data to send,
                converted to binary by struct. Defaults to None.
            blocking (bool, optional): Send message with blocking of other messages. Defaults to True.
            timeout (int, optional): Blocking timeout. Defaults to -1.

        Returns:
            int: Total bytes sent
        """
        buff = out_message_builder(code, fields=data)

        if self.serial_write_lock.acquire(blocking, timeout):
            try:
                sent_bytes = self.serial.write(buff)
            except Exception as e:
                logger.exception("Error writing to serial port", exc_info=e)
            finally:
                self.serial_write_lock.release()
                if sent_bytes > 0:
                    logger.debug("RAW message sent: {}".format(buff))

                return sent_bytes

    def receive_msg(self):

        with self.serial_read_lock:
            # TODO: do this mo-better
            buff = self.serial.readline()
            logger.debug("RAW message received: {}".format(buff))
            if len(buff) > 0:
                return Message.parse(buff)
            return None


__all__ = ["Board"]
