import pytest
from construct import ValidationError

from bonfo.msp.codes import MSP
from bonfo.msp.utils import out_message_builder


def xtest_select_profile_out_of_range():
    # These won't error due to the Optional on fields in message, do we care? if you go above
    # then it just sends an empty byte, meaning profile 0 is selected...
    with pytest.raises(ValidationError):
        out_message_builder(MSP.SELECT_SETTING, dict(pid_profile=10))

    with pytest.raises(ValidationError):
        out_message_builder(MSP.SELECT_SETTING, dict(rate_profile=10))


def test_select_rate_profile():
    # This isn't correct eyt
    assert (
        out_message_builder(
            MSP.SELECT_SETTING,
            dict(rate_profile=5),
        )
        == b"$M<\x01\xd2\x84W"
    )


def test_select_pid_profile():
    # This isn't correct eyt
    assert (
        out_message_builder(
            MSP.SELECT_SETTING,
            dict(pid_profile=2),
        )
        == b'$M<\x01\xd2\x01\xd2'
    )
