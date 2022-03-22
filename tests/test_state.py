import logging
from construct import Container

from confo.msp.codes import MSP
from confo.msp.structs.message import Message


logger = logging.getLogger(__name__)

# MSP_COPY_PROFILE could be used to duplicate a profile via a command and then fill it out and save the yaml?


def test_config_serialization():
    """
    rc tuning may be a special case and we have to select the profile and then query for the tune.
    Get the initial profile, then cycle through all others, and save individual RC tuning profiles.

    For profiles maybe we know which profile we're operating under and those fields are
    """
    pass
    # MSP.RC_TUNING


# def test_rc_tuning():
#     # RxConfig(serialrx_provider=2, stick_max=1900, stick_center=1500, stick_min=1050, spektrum_sat_bind=0, rx_min_usec=885, rx_max_usec=2115, rc_interpolation=2, rc_interpolation_interval=19, rc_interpolation_channels=2, air_mode_activate_threshold=1250, rx_spi_protocol=0, rx_spi_id=0, rx_spi_rf_channel_count=0, fpv_cam_angle_degrees=40, rc_smoothing_type=1, rc_smoothing_input_cutoff=0, rc_smoothing_derivative_cutoff=0, rc_smoothing_input_type=1, rc_smoothing_derivative_type=3)

#     tuning_bytes = b"\x02l\x07\xdc\x05\x1a\x04\x00u\x03C\x08\x02\x13\xe2\x04\x00\x00\x00\x00\x00\x00(\x02\x01\x00\x00\x01\x03\x00\n"

#     # RcTuning(rc_rate=1.0, rc_expo=0.0, roll_pitch_rate=0, roll_rate=0.7, pitch_rate=0.7, yaw_rate=0.7, dynamic_thr_pid=0.65, throttle_mid=0.5, throttle_expo=0.0, dynamic_thr_breakpofloat=0, rc_yaw_expo=0.0, rcyawrate=1.0, rcpitchrate=1.0, rc_pitch_expo=0.0, roll_rate_limit=1998, pitch_rate_limit=1998, yaw_rate_limit=1998)

#     tuning = RcTuning()
#     bits = tuning.struct.parse(tuning_bytes)
#     # assert bits == dict()


def xtest_frame():
    # process_fc_version
    fc_version_response = b"$M>\x03\x01\x00\x01\x15\x16"
    parts = Message.parse(fc_version_response)
    logger.info(parts)
    assert parts.signature == b"$"
    assert parts.version == "V1"
    assert parts.direction == "IN"
    # Don't like this, why isn't it the enum?
    assert parts.message_type == MSP.FC_VERSION
    # assert parts.header.message_type == "FC_VERSION"

    # assert parts == dict(
    #     header=Container(signature=b"$", version="V1", direction="IN", message_type=MSP.FC_VERSION.value),
    #     fields=Container(major=1, minor=1, patch=1),
    # )

def xtest_fc_variant():
    # Is last byte
    fc_message = b"$M>\x04\x02BTFL\x1a"
    parts = Message.parse(fc_message)
    logger.info(parts)
    assert parts.name == "BTFL"
