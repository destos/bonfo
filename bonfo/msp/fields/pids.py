from dataclasses import dataclass
from typing import Any, Iterable, Optional

from construct import Array, Default, Int8ub, Int16ub, Int32ub
from construct import Optional as CSOptional
from construct import Struct
from construct_typed import csfield

from bonfo.msp.codes import MSP
from bonfo.msp.fields.base import MSPFields
from bonfo.msp.structs import MSPCutoff
from bonfo.msp.versions import MSPVersions

__all__ = ["PidAdvanced", "PidCoefficients"]

PID_COUNT = 5


@dataclass
class PidCoefficients(MSPFields, get_code=MSP.PID):
    pids: Iterable[Any] = csfield(
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
    _unused1: Optional[int] = csfield(CSOptional(Default(Int32ub, 0)), "unknown reserved")
    _unused3: Optional[int] = csfield(CSOptional(Default(Int16ub, 0)), "was pidProfile.yaw_p_limit")
    _unused4: Optional[int] = csfield(CSOptional(Default(Int8ub, 0)), "reserved")
    _unused5: Optional[int] = csfield(CSOptional(Default(Int8ub, 0)), "was vbatPidCompensation")
    feedforward_transition: Optional[int] = csfield(
        MSPCutoff(Int8ub, MSPVersions.V1_44, Default(Int8ub, 0)), "USE_FEEDFORWARD"
    )
    _unused6: Optional[int] = csfield(CSOptional(Default(Int8ub, 0)), "was low byte of dtermSetpointWeight")
    _unused7: Optional[int] = csfield(CSOptional(Default(Int8ub, 0)), "reserved")
    _unused8: Optional[int] = csfield(CSOptional(Default(Int8ub, 0)), "reserved")
    _unused9: Optional[int] = csfield(CSOptional(Default(Int8ub, 0)), "reserved")
    rate_accel_limit: Optional[int] = csfield(Int16ub)
    yaw_rate_accel_limit: Optional[int] = csfield(Int16ub)
    level_angle_limit: Optional[int] = csfield(Int8ub)
    _unused10: Optional[int] = csfield(CSOptional(Default(Int8ub, 0)), "was pidProfile.levelSensitivity")
    iterm_throttle_threshold: Optional[int] = csfield(Int16ub)
    iterm_accelerator_gain: Optional[int] = csfield(Int16ub)
    _unused11: Optional[int] = csfield(CSOptional(Default(Int16ub, 0)), "was dtermSetpointWeight")
    iterm_rotation: Optional[int] = csfield(Int8ub)
    _unused12: Optional[int] = csfield(CSOptional(Default(Int8ub, 0)), "was smart_feedforward")
    iterm_relax: Optional[int] = csfield(Int8ub, "USE_ITERM_RELAX")
    iterm_relax_type: Optional[int] = csfield(Int8ub, "USE_ITERM_RELAX")
    abs_control_gain: Optional[int] = csfield(Int8ub, "USE_ABSOLUTE_CONTROL")
    throttle_boost: Optional[int] = csfield(Int8ub, "USE_THROTTLE_BOOST")
    acro_trainer_angle_limit: Optional[int] = csfield(Int8ub, "USE_ACRO_TRAINER")
    pid_roll_f: Optional[int] = csfield(Int16ub, "pid roll feed forward term")
    pid_pitch_f: Optional[int] = csfield(Int16ub, "pid pitch feed forward term")
    pid_yaw_f: Optional[int] = csfield(Int16ub, "pid yaw feed forward term")
    anti_gravity_mode: Optional[int] = csfield(Int8ub, "Flag?")
    d_min_roll: Optional[int] = csfield(Int8ub, "USE_D_MIN")
    d_min_pitch: Optional[int] = csfield(Int8ub, "USE_D_MIN")
    d_min_yaw: Optional[int] = csfield(Int8ub, "USE_D_MIN")
    d_min_gain: Optional[int] = csfield(Int8ub, "USE_D_MIN")
    d_min_advance: Optional[int] = csfield(Int8ub, "USE_D_MIN")
    use_integrated_yaw: Optional[int] = csfield(Int8ub, "USE_INTEGRATED_YAW_CONTROL")
    integrated_yaw_relax: Optional[int] = csfield(Int8ub, "USE_INTEGRATED_YAW_CONTROL")
    iterm_relax_cutoff: Optional[int] = csfield(MSPCutoff(Int8ub, MSPVersions.V1_42), "USE_ITERM_RELAX")
    motor_output_limit: Optional[int] = csfield(MSPCutoff(Int8ub, MSPVersions.V1_43))
    auto_profile_cell_count: Optional[int] = csfield(MSPCutoff(Int8ub, MSPVersions.V1_43))
    dyn_idle_min_rpm: Optional[int] = csfield(MSPCutoff(Int8ub, MSPVersions.V1_43), "USE_DYN_IDLE")
    feedforward_averaging: Optional[int] = csfield(MSPCutoff(Int8ub, MSPVersions.V1_44), "USE_FEEDFORWARD")
    feedforward_smooth_factor: Optional[int] = csfield(MSPCutoff(Int8ub, MSPVersions.V1_44), "USE_FEEDFORWARD")
    feedforward_boost: Optional[int] = csfield(MSPCutoff(Int8ub, MSPVersions.V1_44), "USE_FEEDFORWARD")
    feedforward_max_rate_limit: Optional[int] = csfield(MSPCutoff(Int8ub, MSPVersions.V1_44), "USE_FEEDFORWARD")
    feedforward_jitter_factor: Optional[int] = csfield(MSPCutoff(Int8ub, MSPVersions.V1_44), "USE_FEEDFORWARD")
    vbat_sag_compensation: Optional[int] = csfield(
        MSPCutoff(Int8ub, MSPVersions.V1_44), "USE_BATTERY_VOLTAGE_SAG_COMPENSATION"
    )
    thrust_linearization: Optional[int] = csfield(MSPCutoff(Int8ub, MSPVersions.V1_44), "USE_THRUST_LINEARIZATION")
