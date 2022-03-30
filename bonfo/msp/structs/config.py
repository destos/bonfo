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

from .adapters import RawSingle, RcFloat

ApiVersion = Struct(
    "msp_protocol" / Int8ub,
    "api_major" / Int8ub,
    "api_minor" / Int8ub,
)

FcVariant = Struct("name" / PaddedString(4, "utf8"))

FcVersion = Struct(
    "major" / Int8ub,
    "minor" / Int8ub,
    "patch" / Int8ub,
)

BuildInfo = Struct()
BoardInfo = Struct()
Uid = Struct("uid" / Array(3, Int32ub))
AccTrim = Struct()
Name = Struct()

Status = Struct(
    "cycle_time" / Int16ub,
    "i2c_error" / Int16ub,
    # sensor flags
    "active_sensors" / Int16ub,
    # mode flags
    "mode" / Int32ub,
    # selected profile
    "profile" / Int8ub,
)

StatusEx = Struct(
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
    # first 32bits of mode flags
    "mode" / Int32ub,
    # selected profile
    "profile" / Int8ub,
    # load percent
    "cpuload" / Int16ub,
    # Total number of profiles
    "profile_count" / Int8ub,
    # Rate profile index
    "profile_index" / Int8ub,
    # length of additional flag bytes
    "additional_mode_bytes" / Int8ub,
    # a continuation of the above mode flags
    "additional_mode" / FixedSized(this.additional_mode_bytes, GreedyBytes),
    # Flags indicating why arming is currently disabled
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
    # configuration state ( reboot required )
    "config_state" / FlagsEnum(Int8ub, REBOOT=1 << 8),
)
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

RawIMU = Struct(
    "accelerometer" / RawSingle,
    "gyroscope" / RawSingle,
    "magnetometer" / RawSingle,
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
    "RawIMU",
]
