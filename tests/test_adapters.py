import pytest
from construct import ValidationError

from bonfo.msp.structs.adapters import SelectPIDProfile, SelectRateProfile


def test_select_pid_profile_selector_byte():
    assert SelectPIDProfile.build(1) == b"\x00"
    assert SelectPIDProfile.build(2) == b"\x01"
    assert SelectPIDProfile.build(3) == b"\x02"
    with pytest.raises(ValidationError):
        SelectPIDProfile.build(4)
    with pytest.raises(ValidationError):
        SelectPIDProfile.build(-1)


def test_select_rate_profile_selector_byte():
    assert SelectRateProfile.build(1) == b"\x80"
    assert SelectRateProfile.build(2) == b"\x81"
    assert SelectRateProfile.build(3) == b"\x82"
    assert SelectRateProfile.build(4) == b"\x83"
    assert SelectRateProfile.build(5) == b"\x84"
    assert SelectRateProfile.build(6) == b"\x85"
    with pytest.raises(ValidationError):
        SelectRateProfile.build(7)
    with pytest.raises(ValidationError):
        SelectRateProfile.build(-1)


def xtest_select_rate_profile_selector_byte_parse():
    assert SelectRateProfile.parse(b'\x85') == 6
