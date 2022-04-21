"""Message structs that deal with the status of the board."""


from dataclasses import dataclass

from construct import Array, FixedSized, FlagsEnum, GreedyBytes, Int8ub, Int16ub, Int16ul, Int32ub, PaddedString, this
from construct_typed import csfield

from ..adapters import BTFLTimestamp, GitHash, Int8ubPlusOne, RawSingle
from ..codes import MSP
from .base import MSPFields


@dataclass
class ApiVersion(MSPFields, get_code=MSP.API_VERSION):
    # Should return a semver for comparisons?
    # First byte is version id 0=1, 1=2?
    # Could validate and alert if 2 is returned
    msp_protocol: int = csfield(Int8ub)
    api_major: int = csfield(Int8ub)
    api_minor: int = csfield(Int8ub)


@dataclass
class FcVariant(MSPFields, get_code=MSP.FC_VARIANT):
    variant: str = csfield(PaddedString(4, "utf8"))


@dataclass
class FcVersion(MSPFields, get_code=MSP.FC_VERSION):
    major: int = csfield(Int8ub)
    minor: int = csfield(Int8ub)
    patch: int = csfield(Int8ub)


@dataclass
class BuildInfo(MSPFields, get_code=MSP.BUILD_INFO):
    date_time: int = csfield(BTFLTimestamp)
    git_hash: int = csfield(GitHash)


@dataclass
class BoardInfo(MSPFields, get_code=MSP.BOARD_INFO):
    pass


@dataclass
class Uid(MSPFields, get_code=MSP.UID):
    """Board UID."""

    uid: int = csfield(Array(3, Int32ub))


@dataclass
class AccTrim(MSPFields, get_code=MSP.ACC_TRIM):
    pass


@dataclass
class Name(MSPFields, get_code=MSP.NAME):
    pass


@dataclass
class Status(MSPFields, get_code=MSP.STATUS):
    """Status is not Used!"""

    cycle_time: int = csfield(Int16ub)
    i2c_error: int = csfield(Int16ub)
    # sensor flags
    active_sensors: int = csfield(Int16ub)
    # mode flags
    mode: int = csfield(Int32ub)
    # selected profile
    profile: int = csfield(Int8ub)


@dataclass
class StatusEx(MSPFields, get_code=MSP.STATUS_EX):
    # cycle time in us
    cycle_time: int = csfield(Int16ub)
    # i2x error counter
    i2c_error: int = csfield(Int16ub)
    # sensor flags
    active_sensors: int = csfield(
        FlagsEnum(
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
        )
    )
    mode: int = csfield(Int32ub)
    # selected profile
    pid_profile: int = csfield(Int8ubPlusOne)
    # load percent
    cpuload: int = csfield(Int16ub)
    # Total number of profiles
    profile_count: int = csfield(Int8ub)
    # Rate profile index
    rate_profile: int = csfield(Int8ubPlusOne)
    # length of additional flag bytes
    additional_mode_bytes: int = csfield(Int8ub)
    # a continuation of the above mode flags
    additional_mode: int = csfield(FixedSized(this.additional_mode_bytes, GreedyBytes))
    arming_disable_flags: int = csfield(
        FlagsEnum(
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
        )
    )
    config_state: int = csfield(FlagsEnum(Int8ub, REBOOT=1 << 8))


@dataclass
class RawIMU(MSPFields, get_code=MSP.RAW_IMU):
    accelerometer: int = csfield(RawSingle)
    gyroscope: int = csfield(RawSingle)
    magnetometer: int = csfield(RawSingle)


@dataclass
class SensorAlignment(MSPFields, get_code=MSP.SENSOR_ALIGNMENT):

    align_gyro: int = csfield(Int8ub)
    align_acc: int = csfield(Int8ub)
    align_mag: int = csfield(Int8ub)
    # if self.conf.is_inav:
    #     "align_opflow" / Int8ub,
    # else:
    # 1.41
    gyro_detection_flags: int = csfield(Int8ub)
    gyro_to_use: int = csfield(Int8ub)
    gyro_1_align: int = csfield(Int8ub)
    gyro_2_align: int = csfield(Int8ub)


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
