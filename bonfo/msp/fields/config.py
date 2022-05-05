"""Message structs that deal with configuring the board."""

from dataclasses import dataclass
from typing import Any

from construct import Container, Int8ub, Int16ub, Union
from construct_typed import csfield

from ..adapters import RcFloat, SelectPIDProfile, SelectRateProfile
from ..codes import MSP
from ..fields.base import MSPFields
from ..structs import MSPCutoff
from ..versions import MSPVersions


@dataclass
class SelectSetting(MSPFields, set_code=MSP.SELECT_SETTING):
    """Select between rate and PID profiles in one message.

    The first bit is a flag to allow switching between updating the PID profile
    or rate profile. They are mutually exclusive.

    PID profiles are limited to 1-3, and rate profiles 1-6.
    Any values over or under those will select pid/rate profile 1.

    This message will not be successful if the board is armed.
    """

    profile: Container[Any] = csfield(Union(None, "pid_profile" / SelectPIDProfile, "rate_profile" / SelectRateProfile))


def SelectPID(pid):
    """SelectPID is a wrapper around a configured SelectSetting instance."""
    return SelectSetting(profile=dict(pid_profile=pid))


def SelectRate(rate):
    """SelectRate is a wrapper around a configured SelectSetting instance."""
    return SelectSetting(profile=dict(rate_profile=rate))


@dataclass
class CopyProfile(MSPFields, set_code=MSP.COPY_PROFILE):
    """Tell one profile to copy to another."""


@dataclass
class EepromWrite(MSPFields, set_code=MSP.EEPROM_WRITE):
    """Save all settings to board EEPROM."""


@dataclass
class RxConfig(MSPFields, get_code=MSP.RX_CONFIG, set_code=MSP.SET_RX_CONFIG):
    """RxConfig."""


@dataclass
class RcTuning(MSPFields, get_code=MSP.RC_TUNING, set_code=MSP.SET_RC_TUNING):
    roll_rate_wat: float = csfield(RcFloat)
    roll_expo: float = csfield(RcFloat)
    # grouped R,P,Yrates
    roll_rate: float = csfield(RcFloat)
    pitch_rate: float = csfield(RcFloat)
    yaw_rate: float = csfield(RcFloat)
    tpa_rate: float = csfield(RcFloat)
    throttle_mid: float = csfield(RcFloat)
    throttle_expo: float = csfield(RcFloat)
    tpa_breakpoint: float = csfield(Int16ub)
    rc_yaw_expo: float = csfield(RcFloat)
    rc_yaw_rate: float = csfield(RcFloat)
    rc_pitch_rate: float = csfield(RcFloat)
    rc_pitch_expo: float = csfield(RcFloat)
    # added in 1.41
    throttle_limit_type: float = csfield(MSPCutoff(RcFloat, MSPVersions.V1_41))
    throttle_limit_percent: float = csfield(MSPCutoff(RcFloat, MSPVersions.V1_41))
    # added in 1.42
    roll_rate_limit: int = csfield(MSPCutoff(Int16ub, MSPVersions.V1_42))
    pitch_rate_limit: int = csfield(MSPCutoff(Int16ub, MSPVersions.V1_42))
    yaw_rate_limit: int = csfield(MSPCutoff(Int16ub, MSPVersions.V1_42))
    # added in 1.43
    rates_type: int = csfield(MSPCutoff(Int8ub, MSPVersions.V1_43))


__all__ = [
    "RxConfig",
    "RcTuning",
    "SelectSetting",
    "EepromWrite",
    "CopyProfile",
]
