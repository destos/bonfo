"""Message structs that deal with the status of the board."""


from dataclasses import dataclass
from functools import cached_property
from typing import Optional, Union

from arrow import Arrow
from construct import (
    Array,
    FixedSized,
    FlagsEnum,
    GreedyBytes,
    Int8ub,
    Int16ub,
    Int16ul,
    Int32ub,
    ListContainer,
    PaddedString,
    this,
)
from construct_typed import FlagsEnumBase, TFlagsEnum, csfield
from semver import VersionInfo

from ..adapters import BTFLTimestamp, GitHash, Int8ubPlusOne, RawSingle
from ..codes import MSP
from ..structs import MSPVersion
from ..versions import MSPMaxSupported, MSPVersions
from .base import MSPFields


@dataclass
class ApiVersion(MSPFields, get_code=MSP.API_VERSION):
    # Should return a semver for comparisons?
    # First byte is version id 0=1, 1=2?
    # Could validate and alert if 2 is returned
    msp_protocol: int = csfield(Int8ub)
    api_major: int = csfield(Int8ub)
    api_minor: int = csfield(Int8ub)

    @cached_property
    def semver(self):
        return VersionInfo(self.msp_protocol, self.api_major, self.api_minor)

    @cached_property
    def supported(self):
        return self.semver <= MSPMaxSupported


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
    date_time: Union[str, Arrow] = csfield(BTFLTimestamp)
    git_hash: str = csfield(GitHash)


class TargetCapabilitiesFlags(FlagsEnumBase):
    HAS_VCP = 1 << 0
    HAS_SOFTSERIAL = 1 << 1
    IS_UNIFIED = 1 << 2
    HAS_FLASH_BOOTLOADER = 1 << 3
    SUPPORTS_CUSTOM_DEFAULTS = 1 << 4
    HAS_CUSTOM_DEFAULTS = 1 << 5
    SUPPORTS_RX_BIND = 1 << 6


class ConfigurationProblemsFlags(FlagsEnumBase):
    ACC_NEEDS_CALIBRATION = 1 << 0
    MOTOR_PROTOCOL_DISABLED = 1 << 1


@dataclass
class BoardInfo(MSPFields, get_code=MSP.BOARD_INFO):
    short_name: str = csfield(PaddedString(4, "utf8"))
    hardware_revision: int = csfield(Int16ub)
    uses_max7456: int = csfield(Int8ub, "if 2, uses a MAX7456")
    target_capabilities: TargetCapabilitiesFlags = csfield(TFlagsEnum(Int8ub, TargetCapabilitiesFlags))
    _target_name_length: int = csfield(Int8ub)
    target_name: str = csfield(PaddedString(this._target_name_length, "utf8"))
    _board_name_length: int = csfield(Int8ub)
    board_name: str = csfield(PaddedString(this._board_name_length, "utf8"))
    _manufacturer_id_length: int = csfield(Int8ub)
    manufacturer_id: str = csfield(PaddedString(this._manufacturer_id_length, "utf8"))
    signature: str = csfield(PaddedString(32, "utf8"))
    mcu_type: int = csfield(Int8ub)
    configuration_state: Optional[int] = csfield(MSPVersion(Int8ub, MSPVersions.V1_42))
    sample_rate: Optional[int] = csfield(MSPVersion(Int16ub, MSPVersions.V1_43), "gyro sample rate")
    configuration_problems: ConfigurationProblemsFlags = csfield(
        MSPVersion(TFlagsEnum(Int32ub, ConfigurationProblemsFlags), MSPVersions.V1_43),
    )


@dataclass
class SetBoardInfo(MSPFields, set_code=MSP.SET_BOARD_INFO):
    _board_name_length: int = csfield(Int8ub)
    board_name: str = csfield(PaddedString(this._board_name_length, "utf8"))


@dataclass
class Uid(MSPFields, get_code=MSP.UID):
    """Board UID."""

    uid: ListContainer[int] = csfield(Array(3, Int32ub))


@dataclass
class Name(MSPFields, get_code=MSP.NAME, set_code=MSP.SET_NAME):
    name: str = csfield(PaddedString(16, "utf8"))


@dataclass
class CombinedBoardInfo:
    name: Optional[Name]
    api: Optional[ApiVersion]
    version: Optional[FcVersion]
    build: Optional[BuildInfo]
    board: Optional[BoardInfo]
    variant: Optional[FcVariant]
    uid: Optional[Uid]


@dataclass
class AccTrim(MSPFields, get_code=MSP.ACC_TRIM):
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
    accelerometer: ListContainer[int] = csfield(RawSingle)
    gyroscope: ListContainer[int] = csfield(RawSingle)
    magnetometer: ListContainer[int] = csfield(RawSingle)


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
