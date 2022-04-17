from dataclasses import dataclass, field
from functools import cached_property, partial

from construct import Array, Int8ub, Int16ub, Struct
from construct_typed import DataclassStruct

from bonfo.msp.codes import MSP
from bonfo.msp.fields.base import BaseFields, Direction

PID_COUNT = 5


class PidCoefficients(BaseFields):
    "PID Coefficient values"
    code = MSP.PID
    direction = Direction.OUT
    struct = Struct(
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
class MSPFields:
    get_code: MSP | None = None
    set_code: MSP | None = None
    fields: DataclassStruct = None

    def __post_init__(self, *args, **kwargs):
        pass

    @cached_property
    def struct(self) -> Struct:
        return Struct(
            *list(
                field.name / field.metadata.get("struct", Int8ub) for field in self.fields.__dataclass_fields__.values()
            )
        )

    @cached_property
    def direction(self):
        if self.get_code is not None and self.set_code is not None:
            return Direction.BOTH
        if self.get_code is None:
            return Direction.IN
        if self.set_code is None:
            return Direction.OUT


unused_field = partial(field, init=False, hash=False, repr=False)


@dataclass
class PidAdvanced:
    unused1: int = unused_field(metadata=dict(struct=Int16ub))
    unused2: int = unused_field(metadata=dict(struct=Int16ub))
    unused3: int = unused_field(metadata=dict(struct=Int16ub * "was pidProfile.yaw_p_limit"))
    unused4: int = unused_field(metadata=dict(struct=Int8ub * "reserved"))
    unused5: int = unused_field(metadata=dict(struct=Int8ub * "was vbatPidCompensation"))
    # if defined(USE_FEEDFORWARD)
    feedforward_transition: int = field(default=0, metadata=dict(struct=Int8ub))
    # endif
    unused6: int = unused_field(metadata=dict(struct=Int8ub * "was low byte of dtermSetpointWeight"))
    unused7: int = unused_field(metadata=dict(struct=Int8ub * "reserved"))
    unused8: int = unused_field(metadata=dict(struct=Int8ub * "reserved"))
    unused9: int = unused_field(metadata=dict(struct=Int8ub * "reserved"))
    rate_accel_limit: int = field(default=0, metadata=dict(struct=Int16ub))
    yaw_rate_accel_limit: int = field(default=0, metadata=dict(struct=Int16ub))
    level_angle_limit: int = field(default=0, metadata=dict(struct=Int8ub))
    unused10: int = unused_field(metadata=dict(struct=Int8ub * "was pidProfile.levelSensitivity"))
    iterm_throttle_threshold: int = field(default=0, metadata=dict(struct=Int16ub))
    iterm_accelerator_gain: int = field(default=0, metadata=dict(struct=Int16ub))
    unused11: int = unused_field(metadata=dict(struct=Int16ub * "was dtermSetpointWeight"))
    iterm_rotation: int = field(default=0, metadata=dict(struct=Int8ub))
    unused12: int = unused_field(metadata=dict(struct=Int8ub * "was smart_feedforward"))
    # if defined(USE_ITERM_RELAX)
    iterm_relax: int = field(default=0, metadata=dict(struct=Int8ub))
    iterm_relax_type: int = field(default=0, metadata=dict(struct=Int8ub))
    # endif
    # if defined(USE_ABSOLUTE_CONTROL)
    abs_control_gain: int = field(default=0, metadata=dict(struct=Int8ub))
    # endif
    # if defined(USE_THROTTLE_BOOST)
    throttle_boost: int = field(default=0, metadata=dict(struct=Int8ub))
    # endif
    # if defined(USE_ACRO_TRAINER)
    acro_trainer_angle_limit: int = field(default=0, metadata=dict(struct=Int8ub))
    # endif
    # Feed forward terms
    pid_roll_f: int = field(default=0, metadata=dict(struct=Int16ub))
    pid_pitch_f: int = field(default=0, metadata=dict(struct=Int16ub))
    pid_yaw_f: int = field(default=0, metadata=dict(struct=Int16ub))

    anti_gravity_mode: int = field(default=0, metadata=dict(struct=Int8ub))
    # if defined(USE_D_MIN)
    d_min_roll: int = field(default=0, metadata=dict(struct=Int8ub))
    d_min_pitch: int = field(default=0, metadata=dict(struct=Int8ub))
    d_min_yaw: int = field(default=0, metadata=dict(struct=Int8ub))
    d_min_gain: int = field(default=0, metadata=dict(struct=Int8ub))
    d_min_advance: int = field(default=0, metadata=dict(struct=Int8ub))
    # endif
    # if defined(USE_INTEGRATED_YAW_CONTROL)
    use_integrated_yaw: int = field(default=0, metadata=dict(struct=Int8ub))
    integrated_yaw_relax: int = field(default=0, metadata=dict(struct=Int8ub))
    # endif
    # if defined(USE_ITERM_RELAX)
    # Added in MSP API 1.42
    iterm_relax_cutoff: int = field(default=0, metadata=dict(struct=Int8ub))
    # endif
    # Added in MSP API 1.43
    motor_output_limit: int = field(default=0, metadata=dict(struct=Int8ub))
    auto_profile_cell_count: int = field(default=0, metadata=dict(struct=Int8ub))
    # if defined(USE_DYN_IDLE)
    dyn_idle_min_rpm: int = field(default=0, metadata=dict(struct=Int8ub))
    # endif
    # Added in MSP API 1.44
    # if defined(USE_FEEDFORWARD)
    feedforward_averaging: int = field(default=0, metadata=dict(struct=Int8ub))
    feedforward_smooth_factor: int = field(default=0, metadata=dict(struct=Int8ub))
    feedforward_boost: int = field(default=0, metadata=dict(struct=Int8ub))
    feedforward_max_rate_limit: int = field(default=0, metadata=dict(struct=Int8ub))
    feedforward_jitter_factor: int = field(default=0, metadata=dict(struct=Int8ub))
    # endif
    # if defined(USE_BATTERY_VOLTAGE_SAG_COMPENSATION)
    vbat_sag_compensation: int = field(default=0, metadata=dict(struct=Int8ub))
    # endif
    # if defined(USE_THRUST_LINEARIZATION)
    thrust_linearization: int = field(default=0, metadata=dict(struct=Int8ub))
    # endif


PidAdvancedTranslator = MSPFields(get_code=MSP.PID_ADVANCED, set_code=MSP.SET_PID_ADVANCED, fields=PidAdvanced)

