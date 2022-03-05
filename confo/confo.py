"""Main module."""

from collections import namedtuple
from typing import NamedTuple
import serial


class Config(NamedTuple):
    api_version: str = "0.0.0"
    flight_controller_identifier: str = ''
    flight_controller_version: str = ''
    version: int = 0
    build_info: str = ''
    multi_type: int = 0
    msp_version: int = 0
    capability: int = 0
    cycle_time: int = 0
    i2c_error: int = 0
    active_sensors: int = 0
    mode: int = 0
    profile: int = 0
    uid: list = [0, 0, 0]
    accelerometer_trims: list = [0, 0]
    name: str = ''
    display_name: str = 'pilot'
    num_profiles: int = 3
    rate_profile: int = 0
    board_type: int = 0
    arming_disable_count: int = 0
    arming_disable_flags: int = 0
    arming_disabled: bool = False
    runaway_takeoff_prevention_disabled: bool = False
    board_identifier: str = ""
    board_version: int = 0
    comm_capabilities: int = 0
    target_name: str = ""
    board_name: str = ""
    manufacturer_id: str = ""
    signature: list = []
    mcu_type_id: int = 255
