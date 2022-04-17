"""Message structs that deal with the status of the board."""


from construct import (
    Array,
    FixedSized,
    FlagsEnum,
    GreedyBytes,
    Int8ub,
    Int16ub,
    Int16ul,
    Int32ub,
    PaddedString,
    Struct,
    this,
)

from ..codes import MSP
from ..fields.base import BaseFields, Direction
from .adapters import BTFLTimestamp, GitHash, Int8ubPlusOne, RawSingle


class ApiVersion(BaseFields):
    code = MSP.API_VERSION
    direction = Direction.BOTH
    struct = Struct(
        "msp_protocol" / Int8ub,
        "api_major" / Int8ub,
        "api_minor" / Int8ub,
    )


class FcVariant(BaseFields):
    code = MSP.FC_VARIANT
    direction = Direction.BOTH
    struct = Struct("variant" / PaddedString(4, "utf8"))


class FcVersion(BaseFields):
    code = MSP.FC_VERSION
    direction = Direction.BOTH
    struct = Struct(
        "major" / Int8ub,
        "minor" / Int8ub,
        "patch" / Int8ub,
    )


class BuildInfo(BaseFields):
    code = MSP.BUILD_INFO
    direction = Direction.BOTH
    struct = Struct("date_time" / BTFLTimestamp, "git_hash" / GitHash)


class BoardInfo(BaseFields):
    code = MSP.BOARD_INFO
    direction = Direction.BOTH
    struct = Struct()


class Uid(BaseFields):
    code = MSP.UID
    direction = Direction.BOTH
    struct = Struct("uid" / Array(3, Int32ub))


class AccTrim(BaseFields):
    code = MSP.ACC_TRIM
    direction = Direction.BOTH
    struct = Struct()


class Name(BaseFields):
    code = MSP.NAME
    direction = Direction.BOTH
    struct = Struct()


class Status(BaseFields):
    """Status is not Used"""

    code = MSP.STATUS
    direction = Direction.BOTH
    struct = Struct(
        "cycle_time" / Int16ub,
        "i2c_error" / Int16ub,
        # sensor flags
        "active_sensors" / Int16ub,
        # mode flags
        "mode" / Int32ub,
        # selected profile
        "profile" / Int8ub,
    )


class StatusEx(BaseFields):
    code = MSP.STATUS_EX
    direction = Direction.BOTH
    struct = Struct(
        # cycle time in us
        "cycle_time" / Int16ub,
        # i2x error counter
        "i2c_error" / Int16ub,
        # sensor flags
        "active_sensors"
        / FlagsEnum(
            Int16ul,
            # bit enum position + flag shift
            ACC=1 << 1,
            BARO=1 << 2 << 1,
            MAG=1 << 3 << 2,
            GPS=1 << 5 << 3,
            RANGEFINDER=1 << 4 << 4,
            GYRO=1 << 0 << 5,
            # v2 sensors
            # SONAR = 1 << 4,
            # GPSMAG = 1 << 6,
        ),
        "mode" / Int32ub,
        # selected profile
        "pid_profile" / Int8ubPlusOne,
        # load percent
        "cpuload" / Int16ub,
        # Total number of profiles
        "profile_count" / Int8ub,
        # Rate profile index
        "rate_profile" / Int8ubPlusOne,
        # length of additional flag bytes
        "additional_mode_bytes" / Int8ub,
        # a continuation of the above mode flags
        "additional_mode" / FixedSized(this.additional_mode_bytes, GreedyBytes),
        "arming_disable_flags"
        / FlagsEnum(
            Int32ub,
            NO_GYRO=1 << 0,
            FAILSAFE=1 << 1,
            RX_FAILSAFE=1 << 2,
            BAD_RX_RECOVERY=1 << 3,
            BOXFAILSAFE=1 << 4,
            RUNAWAY_TAKEOFF=1 << 5,
            CRASH_DETECTED=1 << 6,
            THROTTLE=1 << 7,
            ANGLE=1 << 8,
            BOOT_GRACE_TIME=1 << 9,
            NOPREARM=1 << 10,
            LOAD=1 << 11,
            CALIBRATING=1 << 12,
            CLI=1 << 13,
            CMS_MENU=1 << 14,
            BST=1 << 15,
            MSP=1 << 16,
            PARALYZE=1 << 17,
            GPS=1 << 18,
            RESC=1 << 19,
            RPMFILTER=1 << 20,
            REBOOT_REQUIRED=1 << 21,
            DSHOT_BITBANG=1 << 22,
            ACC_CALIBRATION=1 << 23,
            MOTOR_PROTOCOL=1 << 24,
            ARM_SWITCH=1 << 25,
        ),
        "config_state" / FlagsEnum(Int8ub, REBOOT=1 << 8),
    )


class RawIMU(BaseFields):
    code = MSP.RAW_IMU
    direction = Direction.BOTH
    struct = Struct(
        "accelerometer" / RawSingle,
        "gyroscope" / RawSingle,
        "magnetometer" / RawSingle,
    )


class SensorAlignment(BaseFields):
    code = MSP.SENSOR_ALIGNMENT
    direction = Direction.BOTH
    struct = Struct(
        "align_gyro" / Int8ub,
        "align_acc" / Int8ub,
        "align_mag" / Int8ub,
        # if self.conf.is_inav:
        #     "align_opflow" / Int8ub,
        # else:
        "gyro_detection_flags" / Int8ub,
        "gyro_to_use" / Int8ub,
        "gyro_1_align" / Int8ub,
        "gyro_2_align" / Int8ub,
    )


__all__ = [
    "ApiVersion",
    "FcVariant",
    "FcVersion",
    "BuildInfo",
    "BoardInfo",
    "Uid",
    "AccTrim",
    "Name",
    "Status",
    "StatusEx",
    "SensorAlignment",
    "RawIMU",
]
