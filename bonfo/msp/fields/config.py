"""Message structs that deal with configuring the board."""

from dataclasses import dataclass
from typing import Any

from construct import Container, Int8ub, Int16ub, Struct, Union
from construct_typed import csfield

from ..adapters import RcFloat, SelectPIDProfile, SelectRateProfile
from ..codes import MSP
from ..fields.base import MSPFields


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
    return SelectSetting(profile=dict(pid_profile=pid))


def SelectRate(rate):
    return SelectSetting(profile=dict(rate_profile=rate))


CopyProfile = Struct()
"""Tell one profile to copy to another."""

EepromWrite = Struct()
"""Save all settings."""

RxConfig = Struct()
RcTuning = Struct(
    "roll_rate_wat" / RcFloat,
    "roll_expo" / RcFloat,
    "roll_rate" / RcFloat,
    "pitch_rate" / RcFloat,
    "yaw_rate" / RcFloat,
    "tpa_rate" / RcFloat,
    "throttle_mid" / RcFloat,
    "throttle_expo" / RcFloat,
    "tpa_breakpoint" / Int16ub,
    "yaw_expo" / RcFloat,
    "yaw_rate" / RcFloat,
    "pitch_rate" / RcFloat,
    "pitch_expo" / RcFloat,
    # added in 1.41
    "throttle_limit_type" / RcFloat,
    "throttle_limit_percent" / RcFloat,
    # added in 1.42
    "roll_rate_limit" / Int16ub,
    "pitch_rate_limit" / Int16ub,
    "yaw_rate_limit" / Int16ub,
    # added in 1.43
    "rates_type" / Int8ub,
)


__all__ = [
    "RxConfig",
    "RcTuning",
    "SelectSetting",
    "EepromWrite",
    "CopyProfile",
]
