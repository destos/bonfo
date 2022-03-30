import logging

from bonfo.msp.codes import MSP
from bonfo.msp.message import Message
from bonfo.msp.utils import in_message_builder, out_message_builder

logger = logging.getLogger(__name__)


def test_build_fc_version_msg():
    buff = in_message_builder(MSP.FC_VERSION, fields=dict(major=1, minor=12, patch=21))
    assert buff == b"$M>\x03\x03\x01\x0c\x15\x18"


def xtest_fc_version_msg():
    msg = Message.parse(b"$M<\x01\x03\x01\x0c\x15\x1a")
    packet = msg.packet.value
    assert packet.frame_id == MSP.FC_VERSION
    assert packet.fields == dict(major=1, minor=12, patch=21)


def test_request_fc_version_msg():
    buff = out_message_builder(MSP.FC_VERSION)
    assert buff == b"$M<\x00\x03\x03"


def test_parse_api_version_msg():
    fc_version_response = b"$M>\x03\x01\x00\x01\x15\x16"
    msg = Message.parse(fc_version_response)
    packet = msg.packet.value
    assert msg.crc == 22
    assert msg.message_type == "IN"
    assert packet.frame_id == MSP.API_VERSION
    assert packet.fields == dict(msp_protocol=0, api_major=1, api_minor=21)


def test_fc_variant_request():
    proper_request = b'$M<\x00\x02\x02'
    msg = out_message_builder(MSP.FC_VARIANT, fields=None)
    assert msg == proper_request


def test_fc_variant_response():
    fc_response = b"$M>\x04\x02BTFL\x1a"
    msg = Message.parse(fc_response)
    assert msg.packet.value.fields.name == "BTFL"


def xtest_build_fc_variant():
    buff = in_message_builder(MSP.FC_VARIANT, fields=dict(name="DAMN"))
    assert buff == b"$M<\x04\x02DAMN\x01"


def xtest_status_response():
    fc_response = b"$M>\x16e}\x00\x00\x00!\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x00\x1a\x04\x01\x01\x00\x004"

    msg = Message.parse(fc_response)
    values = msg.packet.value.fields
    assert values is None


def test_status_ex_response():
    fc_response = b"$M>\x16\x96}\x00\x00\x00!\x00\x00\x00\x00\x00\x00\x05\x00\x03\x00\x00\x1a\x04\x01\x01\x00\x00\xc4"

    msg = Message.parse(fc_response)
    # TODO: better tests
    assert msg is not None


def xtest_rc_tuning():
    # b"$M>\x02l\x07\xdc\x05\x1a\x04\x00u\x03C\x08\x02\x13\xe2\x04\x00\x00\x00\x00\x00\x00(\x02\x01\x00\x00\x01\x03\x00"
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
