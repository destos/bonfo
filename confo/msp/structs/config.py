from construct import (
    Array,
    Byte,
    Int8ub,
    Int16ub,
    Int32ub,
    Optional,
    PascalString,
    Struct,
)

from confo.msp.structs.adapters import RcFloat


ApiVersion = Struct(
    "msp_protocol" / Int8ub,
    "api_major" / Int8ub,
    "api_minor" / Int8ub,
)

FcVariant = Struct(
    # "length" / Byte,
    "name"
    / PascalString(Byte, "utf8")
)

FcVersion = Optional(
    Struct(
        "major" / Int8ub,
        "minor" / Int8ub,
        "patch" / Int8ub,
    )
)

BuildInfo = Struct()
BoardInfo = Struct()
Uid = Struct("uid" / Array(3, Int32ub))
AccTrim = Struct()
Name = Struct()
Status = Struct()
StatusEx = Struct()
RxConfig = Struct()
RcTuning = Struct(
    "roll_rate_wat" / RcFloat,
    "roll_expo" / RcFloat,
    "roll_rate" / RcFloat,
    "pitch_rate" / RcFloat,
    "yaw_rate" / RcFloat,
    "tpa_rate" / RcFloat,
    "throttle_mid" / RcFloat,
    "throttle_expo" / RcFloat,
    "tpa_breakpoint" / Int16ub,
    "yaw_expo" / RcFloat,
    "yaw_rate" / RcFloat,
    "pitch_rate" / RcFloat,
    "pitch_expo" / RcFloat,
    # added in 1.41
    "throttle_limit_type" / RcFloat,
    "throttle_limit_percent" / RcFloat,
    # added in 1.42
    "roll_rate_limit" / Int16ub,
    "pitch_rate_limit" / Int16ub,
    "yaw_rate_limit" / Int16ub,
    # added in 1.43
    "rates_type" / Int8ub,
)

SensorAlignment = Struct(
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
    "RxConfig",
    "RcTuning",
    "SensorAlignment",
]
