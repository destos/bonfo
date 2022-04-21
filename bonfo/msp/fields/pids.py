from dataclasses import dataclass
from typing import Any, Optional

from construct import Array, Default, Int8ub, Int16ub, Int32ub
from construct import Optional as CSOptional
from construct import Struct
from construct_typed import csfield

from bonfo.msp.codes import MSP
from bonfo.msp.fields.base import MSPFields
from bonfo.msp.structs import MSPVersion
from bonfo.msp.versions import MSPVersions

PID_COUNT = 5


@dataclass
class PidCoefficients(MSPFields, get_code=MSP.PID):
    pids: list[Any] = csfield(
        Array(
            PID_COUNT,
            Struct(
                "p" / Int8ub,
                "i" / Int8ub,
                "d" / Int8ub,
            ),
        )
    )


@dataclass
class PidAdvanced(MSPFields, get_code=MSP.PID_ADVANCED, set_code=MSP.SET_PID_ADVANCED):
    _unused1: int = csfield(CSOptional(Default(Int32ub, 0)), "unknown reserved")
    _unused3: int = csfield(CSOptional(Default(Int16ub, 0)), "was pidProfile.yaw_p_limit")
    _unused4: int = csfield(CSOptional(Default(Int8ub, 0)), "reserved")
    _unused5: int = csfield(CSOptional(Default(Int8ub, 0)), "was vbatPidCompensation")
    feedforward_transition: int = csfield(MSPVersion(Int8ub, MSPVersions.V1_44, Default(Int8ub, 0)), "USE_FEEDFORWARD")
    _unused6: int = csfield(CSOptional(Default(Int8ub, 0)), "was low byte of dtermSetpointWeight")
    _unused7: int = csfield(CSOptional(Default(Int8ub, 0)), "reserved")
    _unused8: int = csfield(CSOptional(Default(Int8ub, 0)), "reserved")
    _unused9: int = csfield(CSOptional(Default(Int8ub, 0)), "reserved")
    rate_accel_limit: int = csfield(Int16ub)
    yaw_rate_accel_limit: int = csfield(Int16ub)
    level_angle_limit: int = csfield(Int8ub)
    _unused10: int = csfield(CSOptional(Default(Int8ub, 0)), "was pidProfile.levelSensitivity")
    iterm_throttle_threshold: int = csfield(Int16ub)
    iterm_accelerator_gain: int = csfield(Int16ub)
    _unused11: int = csfield(CSOptional(Default(Int16ub, 0)), "was dtermSetpointWeight")
    iterm_rotation: int = csfield(Int8ub)
    _unused12: int = csfield(CSOptional(Default(Int8ub, 0)), "was smart_feedforward")
    iterm_relax: int = csfield(Int8ub, "USE_ITERM_RELAX")
    iterm_relax_type: int = csfield(Int8ub, "USE_ITERM_RELAX")
    abs_control_gain: int = csfield(Int8ub, "USE_ABSOLUTE_CONTROL")
    throttle_boost: int = csfield(Int8ub, "USE_THROTTLE_BOOST")
    acro_trainer_angle_limit: int = csfield(Int8ub, "USE_ACRO_TRAINER")
    pid_roll_f: int = csfield(Int16ub, "pid roll feed forward term")
    pid_pitch_f: int = csfield(Int16ub, "pid pitch feed forward term")
    pid_yaw_f: int = csfield(Int16ub, "pid yaw feed forward term")
    anti_gravity_mode: int = csfield(Int8ub, "Flag?")
    d_min_roll: int = csfield(Int8ub, "USE_D_MIN")
    d_min_pitch: int = csfield(Int8ub, "USE_D_MIN")
    d_min_yaw: int = csfield(Int8ub, "USE_D_MIN")
    d_min_gain: int = csfield(Int8ub, "USE_D_MIN")
    d_min_advance: int = csfield(Int8ub, "USE_D_MIN")
    use_integrated_yaw: int = csfield(Int8ub, "USE_INTEGRATED_YAW_CONTROL")
    integrated_yaw_relax: int = csfield(Int8ub, "USE_INTEGRATED_YAW_CONTROL")
    iterm_relax_cutoff: Optional[int] = csfield(MSPVersion(Int8ub, MSPVersions.V1_42), "USE_ITERM_RELAX")
    motor_output_limit: Optional[int] = csfield(MSPVersion(Int8ub, MSPVersions.V1_43))
    auto_profile_cell_count: Optional[int] = csfield(MSPVersion(Int8ub, MSPVersions.V1_43))
    dyn_idle_min_rpm: Optional[int] = csfield(MSPVersion(Int8ub, MSPVersions.V1_43), "USE_DYN_IDLE")
    feedforward_averaging: Optional[int] = csfield(MSPVersion(Int8ub, MSPVersions.V1_44), "USE_FEEDFORWARD")
    feedforward_smooth_factor: Optional[int] = csfield(MSPVersion(Int8ub, MSPVersions.V1_44), "USE_FEEDFORWARD")
    feedforward_boost: Optional[int] = csfield(MSPVersion(Int8ub, MSPVersions.V1_44), "USE_FEEDFORWARD")
    feedforward_max_rate_limit: Optional[int] = csfield(MSPVersion(Int8ub, MSPVersions.V1_44), "USE_FEEDFORWARD")
    feedforward_jitter_factor: Optional[int] = csfield(MSPVersion(Int8ub, MSPVersions.V1_44), "USE_FEEDFORWARD")
    vbat_sag_compensation: Optional[int] = csfield(
        MSPVersion(Int8ub, MSPVersions.V1_44), "USE_BATTERY_VOLTAGE_SAG_COMPENSATION"
    )
    thrust_linearization: Optional[int] = csfield(MSPVersion(Int8ub, MSPVersions.V1_44), "USE_THRUST_LINEARIZATION")
