import logging
import struct
import time
from enum import IntEnum
from functools import wraps
from threading import Lock

import serial

from .codes import MSP, MSPV2
from .state import Config, DataHandler, RcTuning, RxConfig

"""Main MSP interface, borrows from yamspy heavily"""

logger = logging.getLogger(__name__)


class CONST(IntEnum):
    SIGNATURE_LENGTH = 32
    JUMBO_FRAME_SIZE_LIMIT = 255


def process_to(code):
    class ProcessHandler:
        def __init__(self, fn):
            self.fn = fn

        def __set_name__(self, owner, name):
            # Prevent double-registration
            assert code not in owner._handlers.keys()
            logger.info(f"Decorating {self.fn} and using {owner} for {code}")
            # self.fn.class_name = owner.__name__
            read_bytes = owner.read_bytes
            fn = self.fn

            @wraps(self.fn)
            def result(self, data, *args, **kwargs):
                print(name, data)
                # read bytes helper
                def read(unsigned=True, *read_args, **read_kwargs):
                    return read_bytes(data, unsigned=unsigned, *read_args, **read_kwargs)

                return fn(self, data=data, read=read, *args, **kwargs)

            owner._handlers.update({code: result})

            # then replace ourself with the original method
            setattr(owner, name, result)

    return ProcessHandler


def crc8_dvb_s2(crc, ch):
    """CRC for MSPV2
    *copied from inav-configurator
    """
    crc ^= ch
    for _ in range(8):
        if crc & 0x80:
            crc = ((crc << 1) & 0xFF) ^ 0xD5
        else:
            crc = (crc << 1) & 0xFF
    return crc


def bit_check(mask, bit):
    return ((mask >> bit) % 2) != 0


def convert(val_list, n=16):
    """Convert to n*bits (8 multiple) list

    Parameters
    ----------
    val_list : list
        List with values to be converted

    n: int, optional
        Number of bits (multiple of 8) (default is 16)

    Returns
    -------
    list
        List where each item is the equivalent byte value
    """
    buffer = []
    for val in val_list:
        for i in range(int(n / 8)):
            buffer.append((int(val) >> i * 8) & 255)
    return buffer


class FlightController:
    _handlers = dict()

    # for now
    INAV = False

    def __init__(self, port: str, baudrate: int = 115200, trials=100) -> None:
        self.conf = Config()
        # TODO: register configs for saving/applying
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
                self.basic_info()
                return True

            except serial.SerialException as err:
                logger.warning("Error opening the serial port ({0}): {1}".format(self.serial.port, err), exc_info=err)

            except FileNotFoundError as err:
                logger.warning("Port ({0}) not found: {1}".format(self.serial.port, err), exc_info=err)
            time.sleep(delay)

        return False

    # Messaging
    def send_raw_msg(self, code, data=[], blocking=True, timeout=-1):
        """Send a RAW MSP message through the serial port
        Based on betaflight-configurator (https://git.io/fjRxz)

        Parameters
        ----------
        code : int
            MSP Code

        data: list or bytearray, optional
            Data to be sent (default is [])

        Returns
        -------
        int
            number of bytes of data actually written (including 6 bytes header)
        """

        res = -1

        # Always reserve 6 bytes for protocol overhead
        # $ + M + < + data_length + msg_code + data + msg_crc
        len_data = len(data)
        if code < 255:  # MSP V1
            size = len_data + 6
            checksum = 0

            bufView = bytearray([0] * size)

            bufView[0] = 36  # $
            bufView[1] = 77  # M
            bufView[2] = 60  # <
            bufView[3] = len_data
            bufView[4] = code

            checksum = bufView[3] ^ bufView[4]

            for i in range(len_data):
                bufView[i + 5] = data[i]
                checksum ^= bufView[i + 5]

            bufView[-1] = checksum

        elif code > 255:  # MSP V2
            size = len_data + 9
            checksum = 0
            bufView = bytearray([0] * size)
            bufView[0] = 36  # $
            bufView[1] = 88  # X
            bufView[2] = 60  # <
            bufView[3] = 0  # flag: reserved, set to 0
            bufView[4] = code & 0xFF  # code lower byte
            bufView[5] = (code & 0xFF00) >> 8  # code upper byte
            bufView[6] = len_data & 0xFF  # len_data lower byte
            bufView[7] = (len_data & 0xFF00) >> 8  # len_data upper byte
            for di in range(len_data):
                bufView[8 + di] = data[di]
            for si in range(3, size - 1):
                checksum = crc8_dvb_s2(checksum, bufView[si])
            bufView[-1] = checksum

        if self.serial_write_lock.acquire(blocking, timeout):
            try:
                res = self.serial.write(bufView)
            except Exception as e:
                logger.exception("Error writing to serial port", exc_info=e)
            finally:
                self.serial_write_lock.release()
                if res > 0:
                    logger.debug("RAW message sent: {}".format(bufView))

                return res

    def receive_raw_msg(self, size):
        """Receive multiple bytes at once when it's not a jumbo frame.

        Returns
        -------
        bytes
            data received
        """
        with self.serial_read_lock:  # It's necessary to lock everything because order is important
            local_read = self.serial.read
            while True:
                msg_header = local_read()
                if msg_header:
                    if ord(msg_header) == 36:  # $
                        break

            msg = local_read(size - 1)  # -1 to compensate for the $
            return msg_header + msg

    def process_recv_data(self, dataHandler):
        """Process the dataHandler from receive_msg consuming (pop!) dataHandler.data_view as it goes.
        Based on betaflight-configurator (https://git.io/fjRAV)

        Parameters
        ----------
        dataHandler : dict
            Dictionary generated by receive_msg

        Returns
        -------
        int
            len(data) when successful or -(error type) if not
        """

        data = dataHandler.data_view  # DataView (allowing us to view arrayBuffer as struct/union)
        code = dataHandler.code
        if code == 0:  # code==0 means nothing was received...
            logger.debug("Nothing was received - Code 0")
            return -1
        elif dataHandler.crcError:
            logger.debug("dataHandler has a crcError.")
            return -2
        elif dataHandler.packet_error:
            logger.debug("dataHandler has a packet_error.")
            return -3
        else:
            if not dataHandler.unsupported:
                processor = self._handlers.get(code, None)
                if processor:  # if nothing is found, should be None
                    try:
                        if data:
                            processor(self, data)  # use it..
                            return len(data)
                        else:
                            return 0  # because a valid message may contain no data...
                    except IndexError as err:
                        logger.debug('Received data processing error: {}'.format(err))
                        return -4
                else:
                    logger.debug('Unknown code received: {}'.format(code))
                    return -5
            else:
                logger.debug('FC reports unsupported message error - Code {}'.format(code))
                return -6

    def receive_msg(self):
        # TODO: revamp this
        """Receive an MSP message from the serial port
        Based on betaflight-configurator (https://git.io/fjRAz)

        Returns
        -------
        dataclass
            dataHandler with the received data pre-parsed
        """

        dh = DataHandler()
        print(self.serial.readline())
        received_bytes = self.receive_raw_msg(3)
        dh.last_received_timestamp = time.time()

        local_read = self.serial.read
        with self.serial_read_lock:  # It's necessary to lock everything because order is important
            di = 0
            while True:
                try:
                    data = received_bytes[di]
                    di += 1
                    logger.debug(
                        "State: {1} - byte received (at {0}): {2}".format(dh.last_received_timestamp, dh.state, data)
                    )
                except IndexError:
                    # Instead of crashing everything, let's just ignore this msg...
                    # ... and hope for the best :)
                    logger.debug('IndexError detected on state: {}'.format(dh.state))
                    dh.state = -1

                # it will always fall in the first state by default
                if dh.state == 0:  # sync char 1
                    if data == 36:  # $ - a new MSP message begins with $
                        dh.state = 1

                elif dh.state == 1:  # sync char 2
                    if data == 77:  # M - followed by an M => MSP V1
                        dh.msp_version = 1
                        dh.state = 2
                    elif data == 88:  # X => MSP V2
                        dh.msp_version = 2
                        dh.state = 2
                    else:  # something went wrong, no M received...
                        logger.debug('Something went wrong, no M received.')
                        break  # sends it to the error state

                elif dh.state == 2:  # direction (should be >)
                    dh.unsupported = 0
                    if data == 33:  # !
                        # FC reports unsupported message error
                        logger.debug('FC reports unsupported message error.')
                        dh.unsupported = 1
                        break  # sends it to the error state
                    else:
                        if data == 62:  # > FC to PC
                            dh.message_direction = 1
                        elif data == 60:  # < PC to FC
                            dh.message_direction = 0

                        if dh.msp_version == 1:
                            dh.state = 3
                            received_bytes += local_read(2)
                        elif dh.msp_version == 2:
                            dh.state = 2.1
                            received_bytes += local_read(5)

                elif dh.state == 2.1:  # MSP V2: flag (ignored)
                    dh.flags = data  # 4th byte
                    dh.state = 2.2

                elif dh.state == 2.2:  # MSP V2: code LOW
                    dh.code = data
                    dh.state = 2.3

                elif dh.state == 2.3:  # MSP V2: code HIGH
                    dh.code |= data << 8
                    dh.state = 3.1

                elif dh.state == 3:
                    dh.message_length_expected = data  # 4th byte
                    if dh.message_length_expected == CONST.JUMBO_FRAME_SIZE_LIMIT:
                        logger.debug("JumboFrame received.")
                        dh.messageIsJumboFrame = True

                    # start the checksum procedure
                    dh.message_checksum = data
                    dh.state = 4

                elif dh.state == 3.1:  # MSP V2: msg length LOW
                    dh.message_length_expected = data
                    dh.state = 3.2

                elif dh.state == 3.2:  # MSP V2: msg length HIGH
                    dh.message_length_expected |= data << 8
                    # setup buffer according to the message_length_expected
                    dh.message_buffer_uint8_view = (
                        dh.message_buffer
                    )  # keep same names from betaflight-configurator code
                    if dh.message_length_expected > 0:
                        dh.state = 7
                        received_bytes += local_read(dh.message_length_expected + 2)  # +2 for CRC
                    else:
                        dh.state = 9
                        received_bytes += local_read(2)  # 2 for CRC

                elif dh.state == 4:
                    dh.code = data
                    dh.message_checksum ^= data

                    if dh.message_length_expected > 0:
                        # process payload
                        if dh.messageIsJumboFrame:
                            dh.state = 5
                            received_bytes += local_read()
                        else:
                            received_bytes += local_read(dh.message_length_expected + 1)  # +1 for CRC
                            dh.state = 7
                    else:
                        # no payload
                        dh.state = 9
                        received_bytes += local_read()

                elif dh.state == 5:
                    # this is a JumboFrame
                    dh.message_length_expected = data

                    dh.message_checksum ^= data

                    dh.state = 6
                    received_bytes += local_read()

                elif dh.state == 6:
                    # calculates the JumboFrame size
                    dh.message_length_expected += 256 * data
                    logger.debug("JumboFrame message_length_expected: {}".format(dh.message_length_expected))
                    # There's no way to check for transmission errors here...
                    # In the worst scenario, it will try to read 255 + 256*255 = 65535 bytes

                    dh.message_checksum ^= data

                    dh.state = 7
                    received_bytes += local_read(dh.message_length_expected + 1)  # +1 for CRC

                elif dh.state == 7:
                    # setup buffer according to the message_length_expected
                    dh.message_buffer = bytearray(dh.message_length_expected)
                    dh.message_buffer_uint8_view = (
                        dh.message_buffer
                    )  # keep same names from betaflight-configurator code

                    # payload
                    dh.message_buffer_uint8_view[dh.message_length_received] = data
                    dh.message_checksum ^= data
                    dh.message_length_received += 1

                    if dh.message_length_received == dh.message_length_expected:
                        dh.state = 9
                    else:
                        dh.state = 8

                elif dh.state == 8:
                    # payload
                    dh.message_buffer_uint8_view[dh.message_length_received] = data
                    dh.message_checksum ^= data
                    dh.message_length_received += 1

                    if dh.message_length_received == dh.message_length_expected:
                        dh.state = 9

                elif dh.state == 9:
                    if dh.msp_version == 1:
                        if dh.message_checksum == data:
                            # checksum is correct, message received, store dataview
                            logger.debug(
                                "Message received (length {1}) - Code {0}".format(dh.code, dh.message_length_received)
                            )
                            dh.data_view = dh.message_buffer  # keep same names from betaflight-configurator code
                            return dh
                        else:
                            # wrong checksum
                            logger.debug(
                                'Code: {0} - crc failed (received {1}, calculated {2})'.format(
                                    dh.code, data, dh.message_checksum
                                )
                            )
                            dh.crcError = True
                            break  # sends it to the error state
                    elif dh.msp_version == 2:
                        dh.message_checksum = 0
                        dh.message_checksum = crc8_dvb_s2(dh.message_checksum, 0)  # flag
                        dh.message_checksum = crc8_dvb_s2(dh.message_checksum, dh.code & 0xFF)  # code LOW
                        dh.message_checksum = crc8_dvb_s2(dh.message_checksum, (dh.code & 0xFF00) >> 8)  # code HIGH
                        dh.message_checksum = crc8_dvb_s2(
                            dh.message_checksum, dh.message_length_expected & 0xFF
                        )  #  HIGH
                        dh.message_checksum = crc8_dvb_s2(
                            dh.message_checksum, (dh.message_length_expected & 0xFF00) >> 8
                        )  #  HIGH
                        for si in range(dh.message_length_received):
                            dh.message_checksum = crc8_dvb_s2(dh.message_checksum, dh.message_buffer[si])
                        if dh.message_checksum == data:
                            # checksum is correct, message received, store dataview
                            logger.debug(
                                "Message received (length {1}) - Code {0}".format(dh.code, dh.message_length_received)
                            )
                            dh.data_view = dh.message_buffer  # keep same names from betaflight-configurator code
                            return dh
                        else:
                            # wrong checksum
                            logger.debug(
                                'Code: {0} - crc failed (received {1}, calculated {2})'.format(
                                    dh.code, data, dh.message_checksum
                                )
                            )
                            dh.crcError = True
                            break  # sends it to the error state

            # it means an error occurred
            logger.debug('Error detected on state: {}'.format(dh.state))
            dh.packet_error = 1

            return dh

    @staticmethod
    def read_bytes(data, size=8, unsigned=False, read_as_float=False):
        """Unpack bytes according to size / type

        Parameters
        ----------
        data : bytearray
            Data to be unpacked
        size : int, optional
            Number of bits (8, 16 or 32) (default is 8)
        unsigned : bool, optional
            Indicates if data is unsigned or not (default is False)
        read_as_float: bool, optional
            Indicates if data is read as float or not (default is False)

        Returns
        -------
        int
            unpacked bytes according to input options
        """
        buffer = bytearray()

        for _ in range(int(size / 8)):
            buffer.append(data.pop(0))

        if size == 8:
            unpack_format = 'b'
        elif size == 16:
            if read_as_float:  # for special situations like MSP2_INAV_DEBUG
                unpack_format = 'e'
            else:
                unpack_format = 'h'
        elif size == 32:
            if read_as_float:  # for special situations like MSP2_INAV_DEBUG
                unpack_format = 'f'
            else:
                unpack_format = 'i'

        if unsigned:
            unpack_format = unpack_format.upper()

        return struct.unpack('<' + unpack_format, buffer)[0]

    # Querying the controller
    def basic_info(self):
        """Basic info about the flight controller to distinguish between the many flavours."""
        for code in [MSP.API_VERSION, MSP.FC_VARIANT]:
            if self.send_raw_msg(code, data=[]):
                dataHandler = self.receive_msg()
                self.process_recv_data(dataHandler)

        basic_info_cmd_list = [
            MSP.FC_VERSION,
            MSP.BUILD_INFO,
            MSP.BOARD_INFO,
            MSP.UID,
            MSP.ACC_TRIM,
            MSP.NAME,
            MSP.STATUS,
            MSP.STATUS_EX,
            MSP.RX_CONFIG,
            MSP.RC_TUNING,
        ]
        if self.conf.is_inav:
            basic_info_cmd_list.append(MSPV2.INAV_ANALOG)
            basic_info_cmd_list.append(MSP.VOLTAGE_METER_CONFIG)

        for code in basic_info_cmd_list:
            if self.send_raw_msg(code, data=[]):
                dataHandler = self.receive_msg()
                self.process_recv_data(dataHandler)

    @process_to(MSP.STATUS)
    def process_status(self, read=None, **kwargs):
        self.conf.cycle_time = read(size=16)
        self.conf.i2c_error = read(size=16)
        self.conf.active_sensors = read(size=16)
        self.conf.mode = read(size=32)
        self.conf.profile = read(size=8)

    @process_to(MSP.STATUS_EX)
    def process_status_ex(self, read=None, **kwargs):
        self.conf.cycle_time = read(size=16)
        self.conf.i2c_error = read(size=16)
        self.conf.active_sensors = read(size=16)
        self.conf.mode = read(size=32)

        self.conf.profile = read(size=8)
        self.conf.cpuload = read(size=16)

        if not self.conf.is_inav:
            self.conf.num_profiles = read(size=8)
            self.conf.rate_profile = read(size=8)

            # Read flight mode flags
            byteCount = read(size=8)
            self.conf.flight_mode_flags = []  # this was not implemented on betaflight-configurator
            for _ in range(byteCount):
                # betaflight-configurator would just discard these bytes
                self.conf.flight_mode_flags.append(read(size=8))

            # Read arming disable flags
            self.conf.arming_disable_count = read(size=8)  # Flag count
            self.conf.arming_disable_flags = read(size=32)
        else:
            self.conf.arming_disable_flags = read(size=16)

    @process_to(MSP.RAW_IMU)
    def process_raw_imu(self, read=None, **kwargs):
        # /512 for mpu6050, /256 for mma
        # currently we are unable to differentiate between the sensor types, so we are going with 512
        # And what about SENSOR_CONFIG???
        self.SENSOR_DATA['accelerometer'] = [
            read(size=16, unsigned=False),
            read(size=16, unsigned=False),
            read(size=16, unsigned=False),
        ]

        # properly scaled (INAV and BF use the same * (4 / 16.4))
        # but this is supposed to be RAW, so raw it is!
        self.SENSOR_DATA['gyroscope'][0] = [
            read(size=16, unsigned=False),
            read(size=16, unsigned=False),
            read(size=16, unsigned=False),
        ]

        # no clue about scaling factor (/1090), so raw
        self.SENSOR_DATA['magnetometer'][0] = [
            read(size=16, unsigned=False),
            read(size=16, unsigned=False),
            read(size=16, unsigned=False),
        ]

    @process_to(MSP.SERVO)
    def process_servo(self, data, read, **kwargs):
        servoCount = int(len(data) / 2)
        self.SERVO_DATA = [read(size=16) for _ in range(servoCount)]

    @process_to(MSP.MOTOR)
    def process_motor(self, data, read, **kwargs):
        motorCount = int(len(data) / 2)
        self.MOTOR_DATA = [read(size=16) for i in range(motorCount)]

    @process_to(MSP.RC)
    def process_rc(self, data, read, **kwargs):
        n_channels = int(len(data) / 2)
        self.RC['active_channels'] = n_channels
        self.RC['channels'] = [read(size=16) for i in range(n_channels)]

    # @process_to(MSP.RAW_GPS)
    # def process_raw_gps(self, read=None, **kwargs):
    #     self.GPS_DATA['fix'] = read(size=8)
    #     self.GPS_DATA['numSat'] = read(size=8)
    #     self.GPS_DATA['lat'] = read(size=32, unsigned=False)
    #     self.GPS_DATA['lon'] = read(size=32, unsigned=False)
    #     self.GPS_DATA['alt'] = read(size=16)
    #     self.GPS_DATA['speed'] = read(size=16)
    #     self.GPS_DATA['ground_course'] = read(size=16)

    #     if self.conf.is_inav:
    #         self.GPS_DATA['hdop'] = read(size=16)

    # @process_to(MSP.COMP_GPS)
    # def process_comp_gps(self, read=None, **kwargs):
    #     self.GPS_DATA['distanceToHome'] = read(size=16)
    #     self.GPS_DATA['directionToHome'] = read(size=16)
    #     self.GPS_DATA['update'] = read(size=8)

    # @process_to(MSP.GPSSTATISTICS)
    # def process_gpsstatistics(self, read=None, **kwargs):
    #     self.GPS_DATA['messageDt'] = read(size=16)
    #     self.GPS_DATA['errors'] = read(size=32)
    #     self.GPS_DATA['timeouts'] = read(size=32)
    #     self.GPS_DATA['packetCount'] = read(size=32)
    #     self.GPS_DATA['hdop'] = read(size=16)
    #     self.GPS_DATA['eph'] = read(size=16)
    #     self.GPS_DATA['epv'] = read(size=16)

    # @process_to(MSP.ATTITUDE)
    # def process_attitude(self, read=None, **kwargs):
    #     self.SENSOR_DATA['kinematics'][0] = read(size=16, unsigned=False) / 10.0  # x
    #     self.SENSOR_DATA['kinematics'][1] = read(size=16, unsigned=False) / 10.0  # y
    #     self.SENSOR_DATA['kinematics'][2] = read(size=16, unsigned=False)  # z

    # @process_to(MSP.ALTITUDE)
    # def process_altitude(self, read=None, **kwargs):
    #     self.SENSOR_DATA['altitude'] = round((read(size=32, unsigned=False) / 100.0), 2)  # correct scale factor

    # @process_to(MSP.SONAR)
    # def process_sonar(self, read=None, **kwargs):
    #     self.SENSOR_DATA['sonar'] = read(size=32, unsigned=False)

    # @process_to(MSP.ANALOG)
    # def process_analog(self, read=None, **kwargs):
    #     self.ANALOG['voltage'] = read(size=8) / 10.0
    #     self.ANALOG['mAhdrawn'] = read(size=16)
    #     self.ANALOG['rssi'] = read(size=16)  # 0-1023
    #     self.ANALOG['amperage'] = read(size=16, unsigned=False) / 100  # A
    #     self.ANALOG['last_received_timestamp'] = int(time.time())  # why not monotonic? where is time synchronized?
    #     if not self.conf.is_inav:
    #         self.ANALOG['voltage'] = read(size=16) / 100

    # def process_mspv2_inav_analog(self, read=None, **kwargs):
    #     if self.conf.is_inav:
    #         tmp = read(size=8)
    #         self.ANALOG['battery_full_when_plugged_in'] = True if (tmp & 1) else False
    #         self.ANALOG['use_capacity_thresholds'] = True if ((tmp & 2) >> 1) else False
    #         self.ANALOG['battery_state'] = (tmp & 12) >> 2
    #         self.ANALOG['cell_count'] = (tmp & 0xF0) >> 4

    #         self.ANALOG['voltage'] = read(size=16) / 100
    #         self.ANALOG['amperage'] = read(size=16) / 100  # A
    #         self.ANALOG['power'] = read(size=32) / 100
    #         self.ANALOG['mAhdrawn'] = read(size=32)
    #         self.ANALOG['mWhdrawn'] = read(size=32)
    #         self.ANALOG['battery_remaining_capacity'] = read(size=32)
    #         self.ANALOG['battery_percentage'] = read(size=8)
    #         self.ANALOG['rssi'] = read(size=16)  # 0-1023

    #         # TODO: update both BF and INAV variables
    #         self.BATTERY_STATE['cellCount'] = self.ANALOG['cell_count']

    # @process_to(MSP.VOLTAGE_METERS)
    # def process_voltage_meters(self, read=None, **kwargs):
    #     total_bytes_per_meter = (8 + 8) / 8  # just to make it clear where it comes from...
    #     self.VOLTAGE_METERS = [
    #         {
    #             'id': read(size=8),
    #             'voltage': read(size=8) / 10.0,
    #         }
    #         for _ in range(int(len(data) / total_bytes_per_meter))
    #     ]

    # @process_to(MSP.CURRENT_METERS)
    # def process_current_meters(self, read=None, **kwargs):
    #     total_bytes_per_meter = (8 + 16 + 16) / 8  # just to make it clear where it comes from...
    #     self.CURRENT_METERS = [
    #         {
    #             'id': read(size=8),
    #             'mAhDrawn': read(size=16),  # mAh
    #             'amperage': read(size=16) / 1000,  # A
    #         }
    #         for _ in range(int(len(data) / total_bytes_per_meter))
    #     ]

    # @process_to(MSP.BATTERY_STATE)
    # def process_battery_state(self, read=None, **kwargs):
    #     self.BATTERY_STATE['cellCount'] = read(size=8)
    #     self.BATTERY_STATE['capacity'] = read(size=16)  # mAh
    #     # BATTERY_STATE.voltage = data.readU8() / 10.0; // V
    #     self.BATTERY_STATE['mAhDrawn'] = read(size=16)  # mAh
    #     self.BATTERY_STATE['amperage'] = read(size=16) / 100  # A
    #     self.BATTERY_STATE['batteryState'] = read(size=8)
    #     self.BATTERY_STATE['voltage'] = read(size=16) / 100  # V

    # @process_to(MSP.VOLTAGE_METER_CONFIG)
    # def process_voltage_meter_config(self, read=None, **kwargs):
    #     self.VOLTAGE_METER_CONFIGS = []
    #     if self.conf.is_inav:
    #         voltageMeterConfig = {}
    #         voltageMeterConfig['vbatscale'] = read(size=8) / 10
    #         self.VOLTAGE_METER_CONFIGS.append(voltageMeterConfig)
    #         self.BATTERY_CONFIG['vbatmincellvoltage'] = read(size=8) / 10
    #         self.BATTERY_CONFIG['vbatmaxcellvoltage'] = read(size=8) / 10
    #         self.BATTERY_CONFIG['vbatwarningcellvoltage'] = read(size=8) / 10
    #     else:
    #         voltage_meter_count = read(size=8)

    #         for i in range(voltage_meter_count):
    #             subframe_length = read(size=8)
    #             if subframe_length != 5:
    #                 for j in range(subframe_length):
    #                     read(size=8)
    #             else:
    #                 voltageMeterConfig = {}
    #                 voltageMeterConfig['id'] = read(size=8)
    #                 voltageMeterConfig['sensorType'] = read(size=8)
    #                 voltageMeterConfig['vbatscale'] = read(size=8)
    #                 voltageMeterConfig['vbatresdivval'] = read(size=8)
    #                 voltageMeterConfig['vbatresdivmultiplier'] = read(size=8)

    #                 self.VOLTAGE_METER_CONFIGS.append(voltageMeterConfig)

    # @process_to(MSP.CURRENT_METER_CONFIG)
    # def process_current_meter_config(self, read=None, **kwargs):
    #     self.CURRENT_METER_CONFIGS = []
    #     if self.conf.is_inav:
    #         currentMeterConfig = {}
    #         currentMeterConfig['scale'] = read(size=16)
    #         currentMeterConfig['offset'] = read(size=16)
    #         currentMeterConfig['sensorType'] = read(size=8)
    #         self.CURRENT_METER_CONFIGS.append(currentMeterConfig)
    #         self.BATTERY_CONFIG['capacity'] = read(size=16)
    #     else:
    #         current_meter_count = read(size=8)
    #         for i in range(current_meter_count):
    #             currentMeterConfig = {}
    #             subframe_length = read(size=8)

    #             if subframe_length != 6:
    #                 for j in range(subframe_length):
    #                     read(size=8)
    #             else:
    #                 currentMeterConfig['id'] = read(size=8)
    #                 currentMeterConfig['sensorType'] = read(size=8)
    #                 currentMeterConfig['scale'] = read(size=16, unsigned=False)
    #                 currentMeterConfig['offset'] = read(size=16, unsigned=False)

    #                 self.CURRENT_METER_CONFIGS.append(currentMeterConfig)

    # @process_to(MSP.BATTERY_CONFIG)
    # def process_battery_config(self, read=None, **kwargs):
    #     self.BATTERY_CONFIG['vbatmincellvoltage'] = read(size=8) / 10  # 10-50
    #     self.BATTERY_CONFIG['vbatmaxcellvoltage'] = read(size=8) / 10  # 10-50
    #     self.BATTERY_CONFIG['vbatwarningcellvoltage'] = read(size=8) / 10  # 10-50
    #     self.BATTERY_CONFIG['capacity'] = read(size=16)
    #     self.BATTERY_CONFIG['voltageMeterSource'] = read(size=8)
    #     self.BATTERY_CONFIG['currentMeterSource'] = read(size=8)

    #     self.BATTERY_CONFIG['vbatmincellvoltage'] = read(size=16) / 100
    #     self.BATTERY_CONFIG['vbatmaxcellvoltage'] = read(size=16) / 100
    #     self.BATTERY_CONFIG['vbatwarningcellvoltage'] = read(size=16) / 100

    @process_to(MSP.RC_TUNING)
    def process_rc_tuning(self, data, read=None, **kwargs):
        self.rc_tuning.apply_struct(data)
        # self.rc_tuning.rc_rate = round((read(size=8) / 100.0), 2)
        # self.rc_tuning.rc_expo = round((read(size=8) / 100.0), 2)

        # self.rc_tuning.roll_pitch_rate = 0
        # self.rc_tuning.roll_rate = round((read(size=8) / 100.0), 2)
        # self.rc_tuning.pitch_rate = round((read(size=8) / 100.0), 2)

        # self.rc_tuning.yaw_rate = round((read(size=8) / 100.0), 2)
        # self.rc_tuning.dynamic_thr_pid = round((read(size=8) / 100.0), 2)
        # self.rc_tuning.throttle_mid = round((read(size=8) / 100.0), 2)
        # self.rc_tuning.throttle_expo = round((read(size=8) / 100.0), 2)

        # self.rc_tuning.dynamic_thr_breakpoint = read(size=16)

        # self.rc_tuning.rc_yaw_expo = round((read(size=8) / 100.0), 2)

        # if not self.conf.is_inav:
        #     self.rc_tuning.rcyawrate = round((read(size=8) / 100.0), 2)

        #     self.rc_tuning.rcpitchrate = round((read(size=8) / 100.0), 2)
        #     self.rc_tuning.rc_pitch_expo = round((read(size=8) / 100.0), 2)

        #     self.rc_tuning.throttlelimittype = read(size=8)
        #     self.rc_tuning.throttlelimitpercent = read(size=8)

        #     # TODO: do semver checking instead
        #     if int("".join((self.conf.api_version.rsplit('.')))) >= 1420:
        #         self.rc_tuning.roll_rate_limit = read(size=16)
        #         self.rc_tuning.pitch_rate_limit = read(size=16)
        #         self.rc_tuning.yaw_rate_limit = read(size=16)

    @process_to(MSP.PID)
    def process_pid(self, data, read, **kwargs):
        self.PIDs = [[read(size=8) for _ in range(3)] for _ in range(int(len(data) / 3))]

    @process_to(MSPV2.PID)
    def process_msp2_pid(self, data, read, **kwargs):
        self.PIDs = [[read(size=8) for _ in range(4)] for _ in range(int(len(data) / 4))]

    # @process_to(MSP.ARMING_CONFIG)
    # def process_arming_config(self, read=None, **kwargs):
    #     self.ARMING_CONFIG['auto_disarm_delay'] = read(size=8)
    #     self.ARMING_CONFIG['disarm_kill_switch'] = read(size=8)
    #     if not self.conf.is_inav:
    #         self.ARMING_CONFIG['small_angle'] = read(size=8)

    # @process_to(MSP.LOOP_TIME)
    # def process_loop_time(self, read=None, **kwargs):
    #     if self.conf.is_inav:
    #         self.FC_CONFIG['loopTime'] = read(size=16)

    # @process_to(MSP.MISC)
    # def process_misc(self, data, read, **kwargs):  # 22 bytes
    #     if self.conf.is_inav:
    #         self.MISC['midrc'] = self.rx_conf['midrc'] = read(size=16)
    #         self.MISC['minthrottle'] = self.MOTOR_CONFIG['minthrottle'] = self.read_bytes(
    #             data, size=16, unsigned=True
    #         )  # 0-2000
    #         self.MISC['maxthrottle'] = self.MOTOR_CONFIG['maxthrottle'] = self.read_bytes(
    #             data, size=16, unsigned=True
    #         )  # 0-2000
    #         self.MISC['mincommand'] = self.MOTOR_CONFIG['mincommand'] = self.read_bytes(
    #             data, size=16, unsigned=True
    #         )  # 0-2000
    #         self.MISC['failsafe_throttle'] = read(size=16)  # 1000-2000
    #         self.MISC['gps_type'] = self.GPS_CONFIG['provider'] = read(size=8)
    #         self.MISC['sensors_baudrate'] = self.MISC['gps_baudrate'] = read(size=8)
    #         self.MISC['gps_ubx_sbas'] = self.GPS_CONFIG['ublox_sbas'] = read(size=8)
    #         self.MISC['multiwiicurrentoutput'] = read(size=8)
    #         self.MISC['rssi_channel'] = self.RSSI_CONFIG['channel'] = read(size=8)
    #         self.MISC['placeholder2'] = read(size=8)

    #         self.COMPASS_CONFIG['mag_declination'] = read(size=16, unsigned=False) / 100  # -18000-18000

    #         self.MISC['mag_declination'] = self.COMPASS_CONFIG['mag_declination'] * 10

    #         self.MISC['vbatscale'] = read(size=8)  # 10-200
    #         self.MISC['vbatmincellvoltage'] = read(size=8) / 10  # 10-50
    #         self.MISC['vbatmaxcellvoltage'] = read(size=8) / 10  # 10-50
    #         self.MISC['vbatwarningcellvoltage'] = read(size=8) / 10  # 10-50

    # def process_mspv2_inav_misc(self, read=None, **kwargs):
    #     if self.conf.is_inav:
    #         self.MISC['midrc'] = self.rx_conf['midrc'] = read(size=16)
    #         self.MISC['minthrottle'] = self.MOTOR_CONFIG['minthrottle'] = self.read_bytes(
    #             data, size=16, unsigned=True
    #         )  # 0-2000
    #         self.MISC['maxthrottle'] = self.MOTOR_CONFIG['maxthrottle'] = self.read_bytes(
    #             data, size=16, unsigned=True
    #         )  # 0-2000
    #         self.MISC['mincommand'] = self.MOTOR_CONFIG['mincommand'] = self.read_bytes(
    #             data, size=16, unsigned=True
    #         )  # 0-2000
    #         self.MISC['failsafe_throttle'] = read(size=16)  # 1000-2000
    #         self.MISC['gps_type'] = self.GPS_CONFIG['provider'] = read(size=8)
    #         self.MISC['sensors_baudrate'] = self.MISC['gps_baudrate'] = read(size=8)
    #         self.MISC['gps_ubx_sbas'] = self.GPS_CONFIG['ublox_sbas'] = read(size=8)
    #         self.MISC['rssi_channel'] = self.RSSI_CONFIG['channel'] = read(size=8)

    #         self.MISC['mag_declination'] = read(size=16, unsigned=False) / 10  # -18000-18000
    #         self.MISC['vbatscale'] = read(size=16)
    #         self.MISC['voltage_source'] = read(size=8)
    #         self.MISC['battery_cells'] = read(size=8)
    #         self.MISC['vbatdetectcellvoltage'] = read(size=16) / 100
    #         self.MISC['vbatmincellvoltage'] = read(size=16) / 100
    #         self.MISC['vbatmaxcellvoltage'] = read(size=16) / 100
    #         self.MISC['vbatwarningcellvoltage'] = read(size=16) / 100
    #         self.MISC['battery_capacity'] = read(size=32)
    #         self.MISC['battery_capacity_warning'] = read(size=32)
    #         self.MISC['battery_capacity_critical'] = read(size=32)
    #         self.MISC['battery_capacity_unit'] = 'mWh' if read(size=8) else 'mAh'

    # @process_to(MSP.MOTOR_CONFIG)
    # def process_motor_config(self, read=None, **kwargs):
    #     self.MOTOR_CONFIG['minthrottle'] = read(size=16)  # 0-2000
    #     self.MOTOR_CONFIG['maxthrottle'] = read(size=16)  # 0-2000
    #     self.MOTOR_CONFIG['mincommand'] = read(size=16)  # 0-2000

    #     self.MOTOR_CONFIG['motor_count'] = read(size=8)
    #     self.MOTOR_CONFIG['motor_poles'] = read(size=8)
    #     self.MOTOR_CONFIG['use_dshot_telemetry'] = read(size=8) != 0
    #     self.MOTOR_CONFIG['use_esc_sensor'] = read(size=8) != 0

    # @process_to(MSP.COMPASS_CONFIG)
    # def process_compass_config(self, read=None, **kwargs):
    #     self.COMPASS_CONFIG['mag_declination'] = read(size=16, unsigned=False) / 100  # -18000-18000

    # @process_to(MSP.GPS_CONFIG)
    # def process_gps_config(self, read=None, **kwargs):
    #     self.GPS_CONFIG['provider'] = read(size=8)
    #     self.GPS_CONFIG['ublox_sbas'] = read(size=8)

    #     self.GPS_CONFIG['auto_config'] = read(size=8)
    #     self.GPS_CONFIG['auto_baud'] = read(size=8)

    # @process_to(MSP.GPS_RESCUE)
    # def process_gps_rescue(self, read=None, **kwargs):
    #     self.GPS_RESCUE['angle'] = read(size=16)
    #     self.GPS_RESCUE['initialAltitudeM'] = read(size=16)
    #     self.GPS_RESCUE['descentDistanceM'] = read(size=16)
    #     self.GPS_RESCUE['rescueGroundspeed'] = read(size=16)
    #     self.GPS_RESCUE['throttleMin'] = read(size=16)
    #     self.GPS_RESCUE['throttleMax'] = read(size=16)
    #     self.GPS_RESCUE['throttleHover'] = read(size=16)
    #     self.GPS_RESCUE['sanityChecks'] = read(size=8)
    #     self.GPS_RESCUE['minSats'] = read(size=8)

    # @process_to(MSP.RSSI_CONFIG)
    # def process_rssi_config(self, read=None, **kwargs):
    #     self.RSSI_CONFIG['channel'] = read(size=8)

    # @process_to(MSP.MOTOR_3D_CONFIG)
    # def process_motor_3d_config(self, read=None, **kwargs):
    #     self.MOTOR_3D_CONFIG['deadband3d_low'] = read(size=16)
    #     self.MOTOR_3D_CONFIG['deadband3d_high'] = read(size=16)
    #     self.MOTOR_3D_CONFIG['neutral'] = read(size=16)

    # @process_to(MSP.BOXNAMES)
    # def process_boxnames(self, data=None, read=None, **kwargs):
    #     self.AUX_CONFIG = []  # empty the array as new data is coming in

    #     buff = ""
    #     for i in range(len(data)):
    #         char = read(size=8)
    #         if char == 0x3B:  # ; (delimeter char)
    #             self.AUX_CONFIG.append(buff)  # convert bytes into ASCII and save as strings

    #             # empty buffer
    #             buff = ""
    #         else:
    #             buff += chr(char)

    # @process_to(MSP.PIDNAMES)
    # def process_pidnames(self, data=None, read=None, **kwargs):
    #     self.PIDNAMES = []  # empty the array as new data is coming in

    #     buff = ""
    #     for i in range(len(data)):
    #         char = read(size=8)
    #         if char == 0x3B:  # ; (delimeter char)
    #             self.PIDNAMES.append(buff)  # convert bytes into ASCII and save as strings

    #             # empty buffer
    #             buff = ""
    #         else:
    #             buff += chr(char)

    # @process_to(MSP.BOXIDS)
    # def process_boxids(self, data=None, read=None, **kwargs):
    #     self.AUX_CONFIG_IDS = []  # empty the array as new data is coming in

    #     for i in range(len(data)):
    #         self.AUX_CONFIG_IDS.append(read(size=8))

    # @process_to(MSP.SERVO_CONFIGURATIONS)
    # def process_servo_configurations(self, data=None, read=None, **kwargs):
    #     self.SERVO_CONFIG = []  # empty the array as new data is coming in
    #     if len(data) % 12 == 0:
    #         for i in range(0, len(data), 12):
    #             arr = {
    #                 'min': read(size=16),
    #                 'max': read(size=16),
    #                 'middle': read(size=16),
    #                 'rate': read(size=8, unsigned=False),
    #                 'indexOfChannelToForward': read(size=8),
    #                 'reversedInputSources': read(size=32),
    #             }

    #             self.SERVO_CONFIG.append(arr)

    @process_to(MSP.RC_DEADBAND)
    def process_rc_deadband(self, read=None, **kwargs):
        self.RC_DEADBAND_CONFIG['deadband'] = read(size=8)
        self.RC_DEADBAND_CONFIG['yaw_deadband'] = read(size=8)
        self.RC_DEADBAND_CONFIG['alt_hold_deadband'] = read(size=8)

        self.RC_DEADBAND_CONFIG['deadband3d_throttle'] = read(size=16)

    @process_to(MSP.SENSOR_ALIGNMENT)
    def process_sensor_alignment(self, read=None, **kwargs):
        self.SENSOR_ALIGNMENT['align_gyro'] = read(size=8)
        self.SENSOR_ALIGNMENT['align_acc'] = read(size=8)
        self.SENSOR_ALIGNMENT['align_mag'] = read(size=8)

        if self.conf.is_inav:
            self.SENSOR_ALIGNMENT['align_opflow'] = read(size=8)
        else:
            self.SENSOR_ALIGNMENT['gyro_detection_flags'] = read(size=8)
            self.SENSOR_ALIGNMENT['gyro_to_use'] = read(size=8)
            self.SENSOR_ALIGNMENT['gyro_1_align'] = read(size=8)
            self.SENSOR_ALIGNMENT['gyro_2_align'] = read(size=8)

    @process_to(MSP.DISPLAYPORT)
    def process_displayport(self, read=None, **kwargs):
        logger.debug('Displayport values updated')

    @process_to(MSP.SET_RAW_RC)
    def process_set_raw_rc(self, read=None, **kwargs):
        logger.debug('RAW RC values updated')

    @process_to(MSP.SET_PID)
    def process_set_pid(self, read=None, **kwargs):
        logger.info('PID settings saved')

    @process_to(MSP.SET_RC_TUNING)
    def process_set_rc_tuning(self, read=None, **kwargs):
        logger.info('RC Tuning saved')

    @process_to(MSP.ACC_CALIBRATION)
    def process_acc_calibration(self, read=None, **kwargs):
        logger.info('Accel calibration executed')

    @process_to(MSP.MAG_CALIBRATION)
    def process_mag_calibration(self, read=None, **kwargs):
        logger.info('Mag calibration executed')

    @process_to(MSP.SET_MOTOR_CONFIG)
    def process_set_motor_config(self, read=None, **kwargs):
        logger.info('Motor Configuration saved')

    @process_to(MSP.SET_GPS_CONFIG)
    def process_set_gps_config(self, read=None, **kwargs):
        logger.info('GPS Configuration saved')

    @process_to(MSP.SET_RSSI_CONFIG)
    def process_set_rssi_config(self, read=None, **kwargs):
        logger.info('RSSI Configuration saved')

    @process_to(MSP.SET_FEATURE_CONFIG)
    def process_set_feature_config(self, read=None, **kwargs):
        logger.info('Features saved')

    @process_to(MSP.SET_BEEPER_CONFIG)
    def process_set_beeper_config(self, read=None, **kwargs):
        logger.info('Beeper Configuration saved')

    @process_to(MSP.RESET_CONF)
    def process_reset_conf(self, read=None, **kwargs):
        logger.info('Settings Reset')

    @process_to(MSP.SELECT_SETTING)
    def process_select_setting(self, read=None, **kwargs):
        logger.info('Profile selected')

    @process_to(MSP.SET_SERVO_CONFIGURATION)
    def process_set_servo_configuration(self, read=None, **kwargs):
        logger.info('Servo Configuration saved')

    @process_to(MSP.EEPROM_WRITE)
    def process_eeprom_write(self, read=None, **kwargs):
        logger.info('Settings Saved in EEPROM')

    @process_to(MSP.SET_CURRENT_METER_CONFIG)
    def process_set_current_meter_config(self, read=None, **kwargs):
        logger.info('Amperage Settings saved')

    @process_to(MSP.SET_VOLTAGE_METER_CONFIG)
    def process_set_voltage_meter_config(self, read=None, **kwargs):
        logger.info('Voltage config saved')

    @process_to(MSP.DEBUG)
    def process_debug(self, read=None, **kwargs):
        for i in range(4):
            self.SENSOR_DATA['debug'][i] = read(size=16, unsigned=False)

    def process_msp2_inav_debug(self, read=None, **kwargs):
        for i in range(8):
            self.SENSOR_DATA['debug'][i] = read(size=32, unsigned=False)

    @process_to(MSP.SET_MOTOR)
    def process_set_motor(self, read=None, **kwargs):
        logger.info('Motor Speeds Updated')

    @process_to(MSP.UID)
    def process_uid(self, read=None, **kwargs):
        for i in range(3):
            self.conf.uid[i] = read(size=32)

    @process_to(MSP.ACC_TRIM)
    def process_acc_trim(self, read=None, **kwargs):
        self.conf.accelerometer_trims = [
            read(size=16, unsigned=False),  # pitch
            read(size=16, unsigned=False),  # roll
        ]

    @process_to(MSP.SET_ACC_TRIM)
    def process_set_acc_trim(self, read=None, **kwargs):
        logger.info('Accelerometer trimms saved.')

    @process_to(MSP.GPS_SV_INFO)
    def process_gps_sv_info(self, data=None, read=None, **kwargs):
        if len(data) > 0:
            numCh = read(size=8)

            for i in range(numCh):
                self.GPS_DATA['chn'].append(read(size=8))
                self.GPS_DATA['svid'].append(read(size=8))
                self.GPS_DATA['quality'].append(read(size=8))
                self.GPS_DATA['cno'].append(read(size=8))

    @process_to(MSP.RX_MAP)
    def process_rx_map(self, data=None, read=None, **kwargs):
        self.RC_MAP = []  # empty the array as new data is coming in

        for i in range(len(data)):
            self.RC_MAP.append(read(size=8))

    @process_to(MSP.SET_RX_MAP)
    def process_set_rx_map(self, read=None, **kwargs):
        logger.debug('RCMAP saved')

    # @process_to(MSP.MIXER_CONFIG)
    # def process_mixer_config(self, read=None, **kwargs):
    #     self.MIXER_CONFIG['mixer'] = read(size=8)
    #     if not self.conf.is_inav:
    #         self.MIXER_CONFIG['reverseMotorDir'] = read(size=8)

    # @process_to(MSP.FEATURE_CONFIG)
    # def process_feature_config(self, read=None, **kwargs):
    #     self.FEATURE_CONFIG['featuremask'] = read(size=32)
    #     for idx in range(32):
    #         enabled = self.bit_check(self.FEATURE_CONFIG['featuremask'], idx)
    #         if idx in self.FEATURE_CONFIG['features'].keys():
    #             self.FEATURE_CONFIG['features'][idx]['enabled'] = enabled
    #         else:
    #             self.FEATURE_CONFIG['features'][idx] = {'enabled': enabled}

    # @process_to(MSP.BEEPER_CONFIG)
    # def process_beeper_config(self, read=None, **kwargs):
    #     self.BEEPER_CONFIG['beepers'] = read(size=32)

    #     self.BEEPER_CONFIG['dshotBeaconTone'] = read(size=8)

    #     self.BEEPER_CONFIG['dshotBeaconConditions'] = read(size=32)

    # @process_to(MSP.BOARD_ALIGNMENT_CONFIG)
    # def process_board_alignment_config(self, read=None, **kwargs):
    #     self.BOARD_ALIGNMENT_CONFIG['roll'] = read(size=16, unsigned=False)  # -180 - 360
    #     self.BOARD_ALIGNMENT_CONFIG['pitch'] = read(size=16, unsigned=False)  # -180 - 360
    #     self.BOARD_ALIGNMENT_CONFIG['yaw'] = read(size=16, unsigned=False)  # -180 - 360

    # @process_to(MSP.SET_REBOOT)
    # def process_set_reboot(self, read=None, **kwargs):
    #     rebootType = read(size=8)

    #     if (rebootType == self.REBOOT_TYPES['MSC']) or (rebootType == self.REBOOT_TYPES['MSC_UTC']):
    #         if read(size=8) == 0:
    #             logger.warning('Storage device not ready for reboot.')

    #     logger.info('Reboot request accepted')

    @process_to(MSP.API_VERSION)
    def process_api_version(self, read=None, **kwargs):
        self.conf.msp_protocol_version = read(size=8)
        self.conf.api_version = str(read(size=8)) + '.' + str(read(size=8)) + '.0'

    @process_to(MSP.FC_VARIANT)
    def process_fc_variant(self, read=None, **kwargs):
        identifier = ''
        for i in range(4):
            identifier += chr(read(size=8))
        self.conf.flight_controller_identifier = identifier

    @process_to(MSP.FC_VERSION)
    def process_fc_version(self, read=None, **kwargs):
        self.conf.flight_controller_version = str(read(size=8)) + '.'
        self.conf.flight_controller_version += str(read(size=8)) + '.'
        self.conf.flight_controller_version += str(read(size=8))

    @process_to(MSP.BUILD_INFO)
    def process_build_info(self, read=None, **kwargs):
        dateLength = 11
        buff = []
        for i in range(dateLength):
            buff.append(read(size=8))

        buff.append(32)  # ascii space

        timeLength = 8
        for i in range(timeLength):
            buff.append(read(size=8))

        self.conf.build_info = bytearray(buff).decode("utf-8")

    @process_to(MSP.BOARD_INFO)
    def process_board_info(self, data=None, read=None, **kwargs):
        identifier = ''
        for i in range(4):
            identifier += chr(read(size=8))

        self.conf.board_identifier = identifier
        self.conf.board_version = read(size=16)

        self.conf.board_type = read(size=8)

        self.conf.comm_capabilities = read(size=8)

        length = read(size=8)

        for i in range(length):
            self.conf.target_name += chr(read(size=8))

        if data:
            length = read(size=8)
            for i in range(length):
                self.conf.board_name += chr(read(size=8))

            length = read(size=8)
            for i in range(length):
                self.conf.manufacturer_id += chr(read(size=8))

            for i in range(CONST.SIGNATURE_LENGTH):
                self.conf.signature.append(read(size=8))

            self.conf.mcu_type_id = read(size=8)

    @process_to(MSP.NAME)
    def process_name(self, data=None, read=None, **kwargs):
        while len(data) > 0:
            char = read(size=8)
            self.conf.name += chr(char)

    # @process_to(MSP.SET_CHANNEL_FORWARDING)
    # def process_set_channel_forwarding(self,  read=None, **kwargs):
    #     logger.info('Channel forwarding saved')

    # @process_to(MSP.CF_SERIAL_CONFIG)
    # def process_cf_serial_config(self, data=None, read=None, **kwargs):
    #     self.SERIAL_CONFIG['ports'] = []
    #     bytesPerPort = 1 + 2 + (1 * 4)
    #     serialPortCount = int(len(data) / bytesPerPort)

    #     for i in range(serialPortCount):
    #         serialPort = {
    #             'identifier': read(size=8),
    #             'functions': self.serialPortFunctionMaskToFunctions(read(size=16)),
    #             'msp_baudrate': self.BAUD_RATES[read(size=8)],
    #             'gps_baudrate': self.BAUD_RATES[read(size=8)],
    #             'telemetry_baudrate': self.BAUD_RATES[read(size=8)],
    #             'blackbox_baudrate': self.BAUD_RATES[read(size=8)],
    #         }

    #         self.SERIAL_CONFIG['ports'].append(serialPort)

    # @process_to(MSP.SET_CF_SERIAL_CONFIG)
    # def process_set_cf_serial_config(self, read=None, **kwargs):
    #     logger.info('Serial config saved')

    # @process_to(MSP.MODE_RANGES)
    # def process_mode_ranges(self, data=None, read=None, **kwargs):
    #     self.MODE_RANGES = []  # empty the array as new data is coming in

    #     modeRangeCount = int(len(data) / 4)  # 4 bytes per item.

    #     for i in range(modeRangeCount):
    #         modeRange = {
    #             'id': read(size=8),
    #             'auxChannelIndex': read(size=8),
    #             'range': {
    #                 'start': 900 + (read(size=8) * 25),
    #                 'end': 900 + (read(size=8) * 25),
    #             },
    #         }
    #         self.MODE_RANGES.append(modeRange)

    # @process_to(MSP.MODE_RANGES_EXTRA)
    # def process_mode_ranges_extra(self, read=None, **kwargs):
    #     self.MODE_RANGES_EXTRA = []  # empty the array as new data is coming in

    #     modeRangeExtraCount = read(size=8)

    #     for i in range(modeRangeExtraCount):
    #         modeRangeExtra = {
    #             'id': read(size=8),
    #             'modeLogic': read(size=8),
    #             'linkedTo': read(size=8),
    #         }
    #         self.MODE_RANGES_EXTRA.append(modeRangeExtra)

    # @process_to(MSP.ADJUSTMENT_RANGES)
    # def process_adjustment_ranges(self, data=None, read=None, **kwargs):
    #     self.ADJUSTMENT_RANGES = []  # empty the array as new data is coming in

    #     adjustmentRangeCount = int(len(data) / 6)  # 6 bytes per item.

    #     for i in range(adjustmentRangeCount):
    #         adjustmentRange = {
    #             'slotIndex': read(size=8),
    #             'auxChannelIndex': read(size=8),
    #             'range': {
    #                 'start': 900 + (read(size=8) * 25),
    #                 'end': 900 + (read(size=8) * 25),
    #             },
    #             'adjustmentFunction': read(size=8),
    #             'auxSwitchChannelIndex': read(size=8),
    #         }
    #         self.ADJUSTMENT_RANGES.append(adjustmentRange)

    @process_to(MSP.RX_CONFIG)
    def process_rx_config(self, read=None, **kwargs):
        self.rx_conf.serialrx_provider = read(size=8)
        # maxcheck for INAV
        self.rx_conf.stick_max = read(size=16)
        # midrc for INAV
        self.rx_conf.stick_center = read(size=16)
        # mincheck for INAV
        self.rx_conf.stick_min = read(size=16)
        self.rx_conf.spektrum_sat_bind = read(size=8)
        self.rx_conf.rx_min_usec = read(size=16)
        self.rx_conf.rx_max_usec = read(size=16)
        self.rx_conf.rc_interpolation = read(size=8)
        self.rx_conf.rc_interpolation_interval = read(size=8)
        self.rx_conf.air_mode_activate_threshold = read(size=16)
        # spirx_protocol for INAV
        self.rx_conf.rx_spi_protocol = read(size=8)
        # spirx_id for INAV
        self.rx_conf.rx_spi_id = read(size=32)
        # spirx_channel_count for INAV
        self.rx_conf.rx_spi_rf_channel_count = read(size=8)
        self.rx_conf.fpv_cam_angle_degrees = read(size=8)
        if self.conf.is_inav:
            self.rx_conf.receiver_type = read(size=8)
        else:
            self.rx_conf.rc_interpolation_channels = read(size=8)
            self.rx_conf.rc_smoothing_type = read(size=8)
            self.rx_conf.rc_smoothing_input_cutoff = read(size=8)
            self.rx_conf.rc_smoothing_derivative_cutoff = read(size=8)
            self.rx_conf.rc_smoothing_input_type = read(size=8)
            self.rx_conf.rc_smoothing_derivative_type = read(size=8)

    # @process_to(MSP.FAILSAFE_CONFIG)
    # def process_failsafe_config(self, read=None, **kwargs):
    #     self.FAILSAFE_CONFIG['failsafe_delay'] = read(size=8)
    #     self.FAILSAFE_CONFIG['failsafe_off_delay'] = read(size=8)
    #     self.FAILSAFE_CONFIG['failsafe_throttle'] = read(size=16)
    #     self.FAILSAFE_CONFIG['failsafe_switch_mode'] = read(size=8)
    #     self.FAILSAFE_CONFIG['failsafe_throttle_low_delay'] = read(size=16)
    #     self.FAILSAFE_CONFIG['failsafe_procedure'] = read(size=8)

    # @process_to(MSP.RXFAIL_CONFIG)
    # def process_rxfail_config(self, data=None, read=None, **kwargs):
    #     self.RXFAIL_CONFIG = []  # empty the array as new data is coming in

    #     channelCount = int(len(data) / 3)
    #     for i in range(channelCount):
    #         rxfailChannel = {
    #             'mode': read(size=8),
    #             'value': read(size=16),
    #         }
    #         self.RXFAIL_CONFIG.append(rxfailChannel)

    # @process_to(MSP.ADVANCED_CONFIG)
    # def process_advanced_config(self, read=None, **kwargs):
    #     self.PID_ADVANCED_CONFIG['gyro_sync_denom'] = read(size=8)
    #     self.PID_ADVANCED_CONFIG['pid_process_denom'] = read(size=8)
    #     self.PID_ADVANCED_CONFIG['use_unsyncedPwm'] = read(size=8)
    #     self.PID_ADVANCED_CONFIG['fast_pwm_protocol'] = read(size=8)
    #     self.PID_ADVANCED_CONFIG['motor_pwm_rate'] = read(size=16)

    #     self.PID_ADVANCED_CONFIG['digitalIdlePercent'] = read(size=16) / 100

    # @process_to(MSP.FILTER_CONFIG)
    # def process_filter_config(self, read=None, **kwargs):
    #     self.FILTER_CONFIG['gyro_lowpass_hz'] = read(size=8)
    #     self.FILTER_CONFIG['dterm_lowpass_hz'] = read(size=16)
    #     self.FILTER_CONFIG['yaw_lowpass_hz'] = read(size=16)

    #     self.FILTER_CONFIG['gyro_notch_hz'] = read(size=16)
    #     self.FILTER_CONFIG['gyro_notch_cutoff'] = read(size=16)
    #     self.FILTER_CONFIG['dterm_notch_hz'] = read(size=16)
    #     self.FILTER_CONFIG['dterm_notch_cutoff'] = read(size=16)

    #     self.FILTER_CONFIG['gyro_notch2_hz'] = read(size=16)
    #     self.FILTER_CONFIG['gyro_notch2_cutoff'] = read(size=16)

    #     if not self.conf.is_inav:
    #         self.FILTER_CONFIG['dterm_lowpass_type'] = read(size=8)

    #         self.FILTER_CONFIG['gyro_hardware_lpf'] = read(size=8)

    #         read(size=8)  # must consume this byte

    #         self.FILTER_CONFIG['gyro_lowpass_hz'] = read(size=16)
    #         self.FILTER_CONFIG['gyro_lowpass2_hz'] = read(size=16)
    #         self.FILTER_CONFIG['gyro_lowpass_type'] = read(size=8)
    #         self.FILTER_CONFIG['gyro_lowpass2_type'] = read(size=8)
    #         self.FILTER_CONFIG['dterm_lowpass2_hz'] = read(size=16)

    #         self.FILTER_CONFIG['gyro_32khz_hardware_lpf'] = 0

    #         self.FILTER_CONFIG['dterm_lowpass2_type'] = read(size=8)
    #         self.FILTER_CONFIG['gyro_lowpass_dyn_min_hz'] = read(size=16)
    #         self.FILTER_CONFIG['gyro_lowpass_dyn_max_hz'] = read(size=16)
    #         self.FILTER_CONFIG['dterm_lowpass_dyn_min_hz'] = read(size=16)
    #         self.FILTER_CONFIG['dterm_lowpass_dyn_max_hz'] = read(size=16)
    #     else:
    #         self.FILTER_CONFIG['accNotchHz'] = read(size=16)
    #         self.FILTER_CONFIG['accNotchCutoff'] = read(size=16)
    #         self.FILTER_CONFIG['gyroStage2LowpassHz'] = read(size=16)

    # @process_to(MSP.SET_PID_ADVANCED)
    # def process_set_pid_advanced(self, read=None, **kwargs):
    #     logger.info("Advanced PID settings saved")

    # @process_to(MSP.PID_ADVANCED)
    # def process_pid_advanced(self, read=None, **kwargs):
    #     self.ADVANCED_TUNING['rollPitchItermIgnoreRate'] = read(size=16)
    #     self.ADVANCED_TUNING['yawItermIgnoreRate'] = read(size=16)
    #     self.ADVANCED_TUNING['yaw_p_limit'] = read(size=16)
    #     self.ADVANCED_TUNING['deltaMethod'] = read(size=8)
    #     self.ADVANCED_TUNING['vbatPidCompensation'] = read(size=8)
    #     if not self.conf.is_inav:
    #         self.ADVANCED_TUNING['feedforwardTransition'] = read(size=8)

    #         self.ADVANCED_TUNING['dtermSetpointWeight'] = read(size=8)
    #         self.ADVANCED_TUNING['toleranceBand'] = read(size=8)
    #         self.ADVANCED_TUNING['toleranceBandReduction'] = read(size=8)
    #         self.ADVANCED_TUNING['itermThrottleGain'] = read(size=8)
    #         self.ADVANCED_TUNING['pidMaxVelocity'] = read(size=16)
    #         self.ADVANCED_TUNING['pidMaxVelocityYaw'] = read(size=16)

    #         self.ADVANCED_TUNING['levelAngleLimit'] = read(size=8)
    #         self.ADVANCED_TUNING['levelSensitivity'] = read(size=8)

    #         self.ADVANCED_TUNING['itermThrottleThreshold'] = read(size=16)
    #         self.ADVANCED_TUNING['itermAcceleratorGain'] = read(size=16)

    #         self.ADVANCED_TUNING['dtermSetpointWeight'] = read(size=16)

    #         self.ADVANCED_TUNING['itermRotation'] = read(size=8)
    #         self.ADVANCED_TUNING['smartFeedforward'] = read(size=8)
    #         self.ADVANCED_TUNING['itermRelax'] = read(size=8)
    #         self.ADVANCED_TUNING['itermRelaxType'] = read(size=8)
    #         self.ADVANCED_TUNING['absoluteControlGain'] = read(size=8)
    #         self.ADVANCED_TUNING['throttleBoost'] = read(size=8)
    #         self.ADVANCED_TUNING['acroTrainerAngleLimit'] = read(size=8)
    #         self.ADVANCED_TUNING['feedforwardRoll'] = read(size=16)
    #         self.ADVANCED_TUNING['feedforwardPitch'] = read(size=16)
    #         self.ADVANCED_TUNING['feedforwardYaw'] = read(size=16)
    #         self.ADVANCED_TUNING['antiGravityMode'] = read(size=8)

    #         self.ADVANCED_TUNING['dMinRoll'] = read(size=8)
    #         self.ADVANCED_TUNING['dMinPitch'] = read(size=8)
    #         self.ADVANCED_TUNING['dMinYaw'] = read(size=8)
    #         self.ADVANCED_TUNING['dMinGain'] = read(size=8)
    #         self.ADVANCED_TUNING['dMinAdvance'] = read(size=8)
    #         self.ADVANCED_TUNING['useIntegratedYaw'] = read(size=8)
    #         self.ADVANCED_TUNING['integratedYawRelax'] = read(size=8)
    #     else:
    #         self.ADVANCED_TUNING['setpointRelaxRatio'] = read(size=8)
    #         self.ADVANCED_TUNING['dtermSetpointWeight'] = read(size=8)
    #         self.ADVANCED_TUNING['pidSumLimit'] = read(size=16)
    #         self.ADVANCED_TUNING['itermThrottleGain'] = read(size=8)
    #         self.ADVANCED_TUNING['axisAccelerationLimitRollPitch'] = read(size=16)
    #         self.ADVANCED_TUNING['axisAccelerationLimitYaw'] = read(size=16)

    # @process_to(MSP.SENSOR_CONFIG)
    # def process_sensor_config(self, read=None, **kwargs):
    #     self.SENSOR_CONFIG['acc_hardware'] = read(size=8)
    #     self.SENSOR_CONFIG['baro_hardware'] = read(size=8)
    #     self.SENSOR_CONFIG['mag_hardware'] = read(size=8)
    #     if self.conf.is_inav:
    #         self.SENSOR_CONFIG['pitot'] = read(size=8)
    #         self.SENSOR_CONFIG['rangefinder'] = read(size=8)
    #         self.SENSOR_CONFIG['opflow'] = read(size=8)

    # @process_to(MSP.DATAFLASH_SUMMARY)
    # def process_dataflash_summary(self, read=None, **kwargs):
    #     flags = read(size=8)
    #     self.DATAFLASH['ready'] = (flags & 1) != 0
    #     self.DATAFLASH['supported'] = (flags & 2) != 0
    #     self.DATAFLASH['sectors'] = read(size=32)
    #     self.DATAFLASH['totalSize'] = read(size=32)
    #     self.DATAFLASH['usedSize'] = read(size=32)
    #     # update_dataflash_global();

    # @process_to(MSP.DATAFLASH_ERASE)
    # def process_dataflash_erase(self, read=None, **kwargs):
    #     logger.info("Data flash erase begun...")

    # @process_to(MSP.SDCARD_SUMMARY)
    # def process_sdcard_summary(self, read=None, **kwargs):
    #     flags = read(size=8)

    #     self.SDCARD['supported'] = (flags & 0x01) != 0
    #     self.SDCARD['state'] = read(size=8)
    #     self.SDCARD['filesystemLastError'] = read(size=8)
    #     self.SDCARD['freeSizeKB'] = read(size=32)
    #     self.SDCARD['totalSizeKB'] = read(size=32)

    # @process_to(MSP.BLACKBOX_CONFIG)
    # def process_blackbox_config(self, read=None, **kwargs):
    #     if not self.conf.is_inav:
    #         self.BLACKBOX['supported'] = (read(size=8) & 1) != 0
    #         self.BLACKBOX['blackboxDevice'] = read(size=8)
    #         self.BLACKBOX['blackboxRateNum'] = read(size=8)
    #         self.BLACKBOX['blackboxRateDenom'] = read(size=8)

    #         self.BLACKBOX['blackboxPDenom'] = read(size=16)
    #     else:
    #         pass  # API no longer supported (INAV 2.3.0)

    # @process_to(MSP.SET_BLACKBOX_CONFIG)
    # def process_set_blackbox_config(self, read=None, **kwargs):
    #     logger.info("Blackbox config saved")

    # # TODO: This changed and it will need to check the BF version to decode things correctly
    # @process_to(MSP.TRANSPONDER_CONFIG)
    # def process_transponder_config(self, data=None, read=None, **kwargs):
    #     bytesRemaining = len(data)

    #     providerCount = read(size=8)
    #     bytesRemaining -= 1

    #     self.TRANSPONDER['supported'] = providerCount > 0
    #     self.TRANSPONDER['providers'] = []

    #     for i in range(providerCount):
    #         provider = {
    #             'id': read(size=8),
    #             'dataLength': read(size=8),
    #         }
    #         bytesRemaining -= 2

    #         self.TRANSPONDER['providers'].append(provider)

    #     self.TRANSPONDER['provider'] = read(size=8)
    #     bytesRemaining -= 1

    #     self.TRANSPONDER['data'] = []
    #     for i in range(bytesRemaining):
    #         self.TRANSPONDER['data'].append(read(size=8))

    @process_to(MSP.SET_TRANSPONDER_CONFIG)
    def process_set_transponder_config(self, read=None, **kwargs):
        logger.info("Transponder config saved")

    @process_to(MSP.SET_MODE_RANGE)
    def process_set_mode_range(self, read=None, **kwargs):
        logger.info('Mode range saved')

    @process_to(MSP.SET_ADJUSTMENT_RANGE)
    def process_set_adjustment_range(self, read=None, **kwargs):
        logger.info('Adjustment range saved')

    @process_to(MSP.SET_BOARD_ALIGNMENT_CONFIG)
    def process_set_board_alignment_config(self, read=None, **kwargs):
        logger.info('Board alignment saved')

    @process_to(MSP.PID_CONTROLLER)
    def process_pid_controller(self, read=None, **kwargs):
        self.PID['controller'] = read(size=8)

    @process_to(MSP.SET_PID_CONTROLLER)
    def process_set_pid_controller(self, read=None, **kwargs):
        logger.info('PID controller changed')

    @process_to(MSP.SET_LOOP_TIME)
    def process_set_loop_time(self, read=None, **kwargs):
        logger.info('Looptime saved')

    @process_to(MSP.SET_ARMING_CONFIG)
    def process_set_arming_config(self, read=None, **kwargs):
        logger.info('Arming config saved')

    @process_to(MSP.SET_RESET_CURR_PID)
    def process_set_reset_curr_pid(self, read=None, **kwargs):
        logger.info('Current PID profile reset')

    @process_to(MSP.SET_MOTOR_3D_CONFIG)
    def process_set_motor_3d_config(self, read=None, **kwargs):
        logger.info('3D settings saved')

    @process_to(MSP.SET_MIXER_CONFIG)
    def process_set_mixer_config(self, read=None, **kwargs):
        logger.info('Mixer config saved')

    @process_to(MSP.SET_RC_DEADBAND)
    def process_set_rc_deadband(self, read=None, **kwargs):
        logger.info('Rc controls settings saved')

    @process_to(MSP.SET_SENSOR_ALIGNMENT)
    def process_set_sensor_alignment(self, read=None, **kwargs):
        logger.info('Sensor alignment saved')

    @process_to(MSP.SET_RX_CONFIG)
    def process_set_rx_config(self, read=None, **kwargs):
        logger.info('Rx config saved')

    @process_to(MSP.SET_RXFAIL_CONFIG)
    def process_set_rxfail_config(self, read=None, **kwargs):
        logger.info('Rxfail config saved')

    @process_to(MSP.SET_FAILSAFE_CONFIG)
    def process_set_failsafe_config(self, read=None, **kwargs):
        logger.info('Failsafe config saved')

    @process_to(MSP.OSD_CONFIG)
    def process_osd_config(self, read=None, **kwargs):
        logger.info('OSD_CONFIG received')

    @process_to(MSP.SET_OSD_CONFIG)
    def process_set_osd_config(self, read=None, **kwargs):
        logger.info('OSD config set')

    @process_to(MSP.OSD_CHAR_READ)
    def process_osd_char_read(self, read=None, **kwargs):
        logger.info('OSD char received')

    @process_to(MSP.OSD_CHAR_WRITE)
    def process_osd_char_write(self, read=None, **kwargs):
        logger.info('OSD char uploaded')

    @process_to(MSP.VTX_CONFIG)
    def process_vtx_config(self, read=None, **kwargs):
        logger.info('VTX_CONFIG received')

    @process_to(MSP.SET_VTX_CONFIG)
    def process_set_vtx_config(self, read=None, **kwargs):
        logger.info('VTX_CONFIG set')

    @process_to(MSP.SET_NAME)
    def process_set_name(self, read=None, **kwargs):
        logger.info('Name set')

    @process_to(MSP.SET_FILTER_CONFIG)
    def process_set_filter_config(self, read=None, **kwargs):
        logger.info('Filter config set')

    @process_to(MSP.SET_ADVANCED_CONFIG)
    def process_set_advanced_config(self, read=None, **kwargs):
        logger.info('Advanced config parameters set')

    @process_to(MSP.SET_SENSOR_CONFIG)
    def process_set_sensor_config(self, read=None, **kwargs):
        logger.info('Sensor config parameters set')

    @process_to(MSP.COPY_PROFILE)
    def process_copy_profile(self, read=None, **kwargs):
        logger.info('Copy profile')

    @process_to(MSP.ARMING_DISABLE)
    def process_arming_disable(self, read=None, **kwargs):
        logger.info('Arming disable')

    @process_to(MSP.SET_RTC)
    def process_set_rtc(self, read=None, **kwargs):
        logger.info('Real time clock set')
