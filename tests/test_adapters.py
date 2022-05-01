import arrow
import pytest
from construct import ValidationError

from bonfo.msp.adapters import BTFLTimestamp, GitHash, SelectPIDProfile, SelectRateProfile


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


def test_betaflight_timestamp_adapter():
    first_variant = BTFLTimestamp.parse(b"Jan  9 202212:13:14")
    second_variant = BTFLTimestamp.parse(b"Jan 12 202212:13:14")
    assert first_variant == arrow.Arrow(2022, 1, 9, 12, 13, 14)
    assert second_variant == arrow.Arrow(2022, 1, 12, 12, 13, 14)


def test_githash_adapter():
    assert GitHash.parse(b"bad01235678") == "bad0123"


def test_select_rate_profile_selector_byte_parse():
    assert SelectRateProfile.parse(b"\x85") == 6
