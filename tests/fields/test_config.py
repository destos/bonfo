import pytest
from construct import Debugger, ValidationError

from bonfo.msp.fields.config import FeatureConfig, Features, SelectPID, SelectRate, SelectSetting

from .. import messages


def test_select_profile_out_of_range():
    with pytest.raises(ValidationError):
        data = SelectPID(10)
        SelectSetting.get_struct().build(data)

    with pytest.raises(ValidationError):
        data = SelectRate(10)
        SelectSetting.get_struct().build(data)


def test_select_setting_rate_profile_build():
    data = SelectSetting(profile=dict(rate_profile=3))
    assert SelectSetting.get_struct().build(data) == b"\x82"


def test_select_rate_build():
    data = SelectRate(3)
    assert SelectSetting.get_struct().build(data) == b"\x82"


def test_select_setting_pid_profile_build():
    data = SelectSetting(profile=dict(pid_profile=2))
    assert SelectSetting.get_struct().build(data) == b"\x01"


def test_select_pid_build():
    data = SelectPID(3)
    assert SelectSetting.get_struct().build(data) == b"\x02"


def test_feature_config():
    messages.feature_config_response
    # struct = Debugger(FeatureConfig.get_struct())
    struct = FeatureConfig.get_struct()
    struct.parse(messages.feature_config_response)


def test_feature_config_operations():
    pass
    # Test flag manipulation features?
    # |
    # &
    # ^
    rx_gps = sum([Features.RX_SERIAL, Features.GPS])
    rx_gps = Features.RX_SERIAL - Features.GPS

    print(rx_gps)


def xtest_rc_tuning_parse():
    # RcTuning(
    #     rc_rate=1.0,
    #     rc_expo=0.0,
    #     roll_pitch_rate=0,
    #     roll_rate=0.7,
    #     pitch_rate=0.7,
    #     yaw_rate=0.7,
    #     dynamic_thr_pid=0.65,
    #     throttle_mid=0.5,
    #     throttle_expo=0.0,
    #     dynamic_thr_breakpofloat=0,
    #     rc_yaw_expo=0.0,
    #     rcyawrate=1.0,
    #     rcpitchrate=1.0,
    #     rc_pitch_expo=0.0,
    #     roll_rate_limit=1998,
    #     pitch_rate_limit=1998,
    #     yaw_rate_limit=1998,
    # )
    pass


def xtest_rx_config():
    # RxConfig(
    #     serialrx_provider=2,
    #     stick_max=1900,
    #     stick_center=1500,
    #     stick_min=1050,
    #     spektrum_sat_bind=0,
    #     rx_min_usec=885,
    #     rx_max_usec=2115,
    #     rc_interpolation=2,
    #     rc_interpolation_interval=19,
    #     rc_interpolation_channels=2,
    #     air_mode_activate_threshold=1250,
    #     rx_spi_protocol=0,
    #     rx_spi_id=0,
    #     rx_spi_rf_channel_count=0,
    #     fpv_cam_angle_degrees=40,
    #     rc_smoothing_type=1,
    #     rc_smoothing_input_cutoff=0,
    #     rc_smoothing_derivative_cutoff=0,
    #     rc_smoothing_input_type=1,
    #     rc_smoothing_derivative_type=3,
    # )
    pass
