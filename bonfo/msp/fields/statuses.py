"""Message structs that deal with the status of the board."""


from dataclasses import dataclass
from functools import cached_property
from typing import Optional, Union

from arrow import Arrow
from construct import (
    Array,
    FixedSized,
    GreedyBytes,
    Int8ub,
    Int16ub,
    Int16ul,
    Int32ub,
    ListContainer,
    PaddedString,
    this,
)
from construct_typed import EnumBase, FlagsEnumBase, TEnum, TFlagsEnum, csfield
from semver import VersionInfo

from ..adapters import BTFLTimestamp, GitHash, Int8ubPlusOne, RawSingle
from ..codes import MSP
from ..structs import MSPCutoff
from ..versions import MSPMaxSupported, MSPVersions
from .base import MSPFields
from .utils import BIT

__all__ = [
    "ApiVersion",
    "FcVariant",
    "FcVersion",
    "BuildInfo",
    "TargetCapabilitiesFlags",
    "ConfigurationProblemsFlags",
    "BoardInfo",
    "Uid",
    "AccTrim",
    "Name",
    "Status",
    "ActiveSensorsFlags",
    "ArmingDisableFlags",
    "ConfigStateFlags",
    "StatusEx",
    "GyroDetectionFlags",
    "SensorAlignment",
    "RawIMU",
]


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
    HAS_VCP = BIT(0)
    HAS_SOFTSERIAL = BIT(1)
    IS_UNIFIED = BIT(2)
    HAS_FLASH_BOOTLOADER = BIT(3)
    SUPPORTS_CUSTOM_DEFAULTS = BIT(4)
    HAS_CUSTOM_DEFAULTS = BIT(5)
    SUPPORTS_RX_BIND = BIT(6)


class ConfigurationProblemsFlags(FlagsEnumBase):
    ACC_NEEDS_CALIBRATION = BIT(0)
    MOTOR_PROTOCOL_DISABLED = BIT(1)


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
    configuration_state: Optional[int] = csfield(MSPCutoff(Int8ub, MSPVersions.V1_42))
    sample_rate: Optional[int] = csfield(MSPCutoff(Int16ub, MSPVersions.V1_43), "gyro sample rate")
    configuration_problems: ConfigurationProblemsFlags = csfield(
        MSPCutoff(TFlagsEnum(Int32ub, ConfigurationProblemsFlags), MSPVersions.V1_43),
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


class ActiveSensorsFlags(FlagsEnumBase):
    # bit enum position + flag shift
    ACC = 1 << 1
    BARO = 1 << 2 << 1
    MAG = 1 << 3 << 2
    GPS = 1 << 5 << 3
    RANGEFINDER = 1 << 4 << 4
    GYRO = 1 << 0 << 5
    # v2 sensors
    # SONAR = 1 << 4,
    # GPSMAG = 1 << 6,


class ArmingDisableFlags(FlagsEnumBase):
    NO_GYRO = BIT(0)
    FAILSAFE = BIT(1)
    RX_FAILSAFE = BIT(2)
    BAD_RX_RECOVERY = BIT(3)
    BOXFAILSAFE = BIT(4)
    RUNAWAY_TAKEOFF = BIT(5)
    CRASH_DETECTED = BIT(6)
    THROTTLE = BIT(7)
    ANGLE = BIT(8)
    BOOT_GRACE_TIME = BIT(9)
    NOPREARM = BIT(10)
    LOAD = BIT(11)
    CALIBRATING = BIT(12)
    CLI = BIT(13)
    CMS_MENU = BIT(14)
    BST = BIT(15)
    MSP = BIT(16)
    PARALYZE = BIT(17)
    GPS = BIT(18)
    RESC = BIT(19)
    RPMFILTER = BIT(20)
    REBOOT_REQUIRED = BIT(21)
    DSHOT_BITBANG = BIT(22)
    ACC_CALIBRATION = BIT(23)
    MOTOR_PROTOCOL = BIT(24)
    ARM_SWITCH = BIT(25)


class ConfigStateFlags(FlagsEnumBase):
    REBOOT = BIT(8)


@dataclass
class StatusEx(MSPFields, get_code=MSP.STATUS_EX):
    cycle_time: int = csfield(Int16ub, "cycle time in us")
    i2c_error: int = csfield(Int16ub, "i2x error counter")
    active_sensors: ActiveSensorsFlags = csfield(TFlagsEnum(Int16ul, ActiveSensorsFlags), "sensor flags")
    mode: int = csfield(Int32ub)
    pid_profile: int = csfield(Int8ubPlusOne, "Selected pid profile")
    cpuload: int = csfield(Int16ub, "Load percent")
    profile_count: int = csfield(Int8ub, "Total number of profiles")
    rate_profile: int = csfield(Int8ubPlusOne, "Rate profile index")
    additional_mode_bytes: int = csfield(Int8ub, "length of additional flag bytes")
    additional_mode: bytes = csfield(
        FixedSized(this.additional_mode_bytes, GreedyBytes), "a continuation of the above mode flags"
    )
    arming_disable_flags: ArmingDisableFlags = csfield(TFlagsEnum(Int32ub, ArmingDisableFlags))
    config_state: ConfigStateFlags = csfield(TFlagsEnum(Int8ub, ConfigStateFlags))


@dataclass
class RawIMU(MSPFields, get_code=MSP.RAW_IMU):
    accelerometer: ListContainer[int] = csfield(RawSingle)
    gyroscope: ListContainer[int] = csfield(RawSingle)
    magnetometer: ListContainer[int] = csfield(RawSingle)


class GyroDetectionFlags(FlagsEnumBase):
    GYRO_NONE_MASK = 0
    GYRO_1_MASK = BIT(0)
    GYRO_2_MASK = BIT(1)
    GYRO_ALL_MASK = GYRO_1_MASK | GYRO_2_MASK
    GYRO_IDENTICAL_MASK = BIT(7)  # All gyros are of the same hardware type


class SensorAlignEnum(EnumBase):
    """SensorAlignEnum mirror enum defintion from betaflight sensor_alignment.h."""

    ALIGN_DEFAULT = 0  # driver-provided alignment
    # the order of these 8 values also correlate to corresponding code in ALIGNMENT_TO_BITMASK.
    # R, P, Y
    CW0_DEG = 1  # 00,00,00
    CW90_DEG = 2  # 00,00,01
    CW180_DEG = 3  # 00,00,10
    CW270_DEG = 4  # 00,00,11
    CW0_DEG_FLIP = 5  # 00,10,00 # _FLIP = 2x90 degree PITCH rotations
    CW90_DEG_FLIP = 6  # 00,10,01
    CW180_DEG_FLIP = 7  # 00,10,10
    CW270_DEG_FLIP = 8  # 00,10,11
    ALIGN_CUSTOM = 9  # arbitrary sensor angles, e.g. for external sensors


# Alignment mask results as part of masking?
# Maybe the fallback struct resolver that resolve the mask first, if fails returns the enum?


@dataclass
class SensorAlignment(MSPFields, get_code=MSP.SENSOR_ALIGNMENT, set_code=MSP.SET_SENSOR_ALIGNMENT):
    # First byte may be ignored on set?, check msp.c
    align_gyro: SensorAlignEnum = csfield(TEnum(Int8ub, SensorAlignEnum))
    align_acc: SensorAlignEnum = csfield(TEnum(Int8ub, SensorAlignEnum))
    align_mag: SensorAlignEnum = csfield(TEnum(Int8ub, SensorAlignEnum))
    gyro_detection_flags: GyroDetectionFlags = csfield(
        MSPCutoff(TFlagsEnum(Int8ub, GyroDetectionFlags), MSPVersions.V1_41)
    )
    gyro_to_use: int = csfield(MSPCutoff(Int8ubPlusOne, MSPVersions.V1_41))
    gyro_1_align: SensorAlignEnum = csfield(MSPCutoff(TEnum(Int8ub, SensorAlignEnum), MSPVersions.V1_41))
    gyro_2_align: SensorAlignEnum = csfield(MSPCutoff(TEnum(Int8ub, SensorAlignEnum), MSPVersions.V1_41))
