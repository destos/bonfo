import pytest
from construct import Container, ListContainer
from construct_typed import DataclassStruct

from bonfo.msp.codes import MSP
from bonfo.msp.fields.base import Direction
from bonfo.msp.fields.pids import PidAdvanced, PidCoefficients
from bonfo.msp.versions import MSPVersions
from tests import messages
from tests.utils import minus_preamble


def test_pid_coefficients():
    assert PidCoefficients.get_direction() == Direction.OUT
    assert PidCoefficients.get_code == MSP.PID
    assert PidCoefficients.set_code is None
    assert isinstance(PidCoefficients.get_struct(), DataclassStruct)


def test_pid_coefficients_parse():
    data_bytes = minus_preamble(messages.pid)
    data = PidCoefficients.get_struct().parse(data_bytes)
    assert isinstance(data, PidCoefficients)
    assert data == PidCoefficients(
        pids=ListContainer(
            [
                Container(p=22, i=68, d=31),
                Container(p=26, i=68, d=31),
                Container(p=29, i=76, d=4),
                Container(p=53, i=55, d=75),
                Container(p=40, i=0, d=0),
            ]
        )
    )


def test_pid_parse_and_build_non_destructive():
    """Pid advanced generated struct should be non-destructive to bytestring."""
    data_bytes = minus_preamble(messages.pid)
    struct = PidCoefficients.get_struct()
    data = struct.parse(data_bytes)
    assert isinstance(data, PidCoefficients)
    output_data_bytes = struct.build(data)
    assert data_bytes == output_data_bytes


def test_pid_advanced():
    assert PidAdvanced.get_direction() == Direction.BOTH
    assert PidAdvanced.get_code == MSP.PID_ADVANCED
    assert PidAdvanced.set_code == MSP.SET_PID_ADVANCED
    assert isinstance(PidAdvanced.get_struct(), DataclassStruct)


def xtest_pid_advanced_parse():
    data_bytes = minus_preamble(messages.pid_advanced)
    data = PidAdvanced.get_struct().parse(data_bytes, msp=MSPVersions.V1_43)
    assert isinstance(data, PidAdvanced)
    # TODO: don't require unused parameters fields
    assert data == PidAdvanced(
        feedforward_transition=1,
        rate_accel_limit=1,
        yaw_rate_accel_limit=1,
        level_angle_limit=1,
        iterm_throttle_threshold=1,
        iterm_accelerator_gain=1,
        iterm_rotation=1,
        iterm_relax=1,
        iterm_relax_type=1,
        abs_control_gain=1,
        throttle_boost=1,
        acro_trainer_angle_limit=1,
        pid_roll_f=1,
        pid_pitch_f=1,
        pid_yaw_f=1,
        anti_gravity_mode=1,
        d_min_roll=1,
        d_min_pitch=1,
        d_min_yaw=1,
        d_min_gain=1,
        d_min_advance=1,
        use_integrated_yaw=1,
        integrated_yaw_relax=1,
        iterm_relax_cutoff=1,
        motor_output_limit=1,
        auto_profile_cell_count=1,
        dyn_idle_min_rpm=1,
        feedforward_averaging=1,
        feedforward_smooth_factor=1,
        feedforward_boost=1,
        feedforward_max_rate_limit=1,
        feedforward_jitter_factor=1,
        vbat_sag_compensation=1,
        thrust_linearization=1,
    )


def test_pid_advanced_parse_and_build_non_destructive():
    """Pi aAdvanced generated struct should be non-destructive to bytescring."""
    data_bytes = minus_preamble(messages.pid_advanced)
    struct = PidAdvanced.get_struct()
    data = struct.parse(data_bytes, msp=MSPVersions.V1_43.value)
    assert isinstance(data, PidAdvanced)
    output_data_bytes = struct.build(data, msp=MSPVersions.V1_43.value)
    assert data_bytes == output_data_bytes


def test_pid_advanced_dataclass_no_args_errors():
    """No args throws a type error with missing count."""
    with pytest.raises(TypeError) as exec_info:
        PidAdvanced()
    assert "34" in exec_info.exconly()


def test_pid_advanced_dataclass_init_good_data():
    """Pid advanced shouldn't error when initialized."""
    PidAdvanced(
        feedforward_transition=1,
        rate_accel_limit=1,
        yaw_rate_accel_limit=1,
        level_angle_limit=1,
        iterm_throttle_threshold=1,
        iterm_accelerator_gain=1,
        iterm_rotation=1,
        iterm_relax=1,
        iterm_relax_type=1,
        abs_control_gain=1,
        throttle_boost=1,
        acro_trainer_angle_limit=1,
        pid_roll_f=1,
        pid_pitch_f=1,
        pid_yaw_f=1,
        anti_gravity_mode=1,
        d_min_roll=1,
        d_min_pitch=1,
        d_min_yaw=1,
        d_min_gain=1,
        d_min_advance=1,
        use_integrated_yaw=1,
        integrated_yaw_relax=1,
        iterm_relax_cutoff=1,
        motor_output_limit=1,
        auto_profile_cell_count=1,
        dyn_idle_min_rpm=1,
        feedforward_averaging=1,
        feedforward_smooth_factor=1,
        feedforward_boost=1,
        feedforward_max_rate_limit=1,
        feedforward_jitter_factor=1,
        vbat_sag_compensation=1,
        thrust_linearization=1,
    )
