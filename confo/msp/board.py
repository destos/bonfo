import logging
import serial
import time
from threading import Lock

from confo.msp.codes import MSP
from confo.msp.structs import Message

from .state import Config, RcTuning, RxConfig


logger = logging.getLogger(__name__)


class Board:
    def __init__(self, port: str, baudrate: int = 115200, trials=100) -> None:
        self.conf = Config()

        # TODO: register configs for saving/applying?
        self.rx_conf = RxConfig()
        self.rc_tuning = RcTuning()

        self.serial_trials = trials
        self.serial_write_lock = Lock()
        self.serial_read_lock = Lock()

        self.init_serial(port, baudrate=baudrate)

    def init_serial(self, port: str, baudrate: int = 115200):
        self.serial = serial.Serial(
            port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
            writeTimeout=1,
        )
        logger.debug(self.serial)

    def __enter__(self):
        self.is_serial_open = self.connect(trials=self.serial_trials)

        if self.is_serial_open:
            return self
        else:
            logger.warning("Serial port ({}) not ready/available".format(self.serial.port))
            return False

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.serial.closed:
            self.serial.close()

    def connect(self, trials=100, delay=0.5):
        """Opens the serial connection with the board"""

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


    def send_msg(self, code: MSP, data=dict(), blocking=True, timeout=-1):
        buff = Message.build(dict(header=dict(frame_id=code, message_type="OUT"), fields=data))
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
        return Message.parse(self.serial.readline())
