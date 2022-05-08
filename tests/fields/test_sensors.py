from construct_typed import DataclassStruct

from bonfo.msp.fields.base import Direction
from bonfo.msp.fields.sensors import Attitude
from tests import messages
from tests.utils import minus_preamble


def test_attitude():
    assert isinstance(Attitude.get_struct(), DataclassStruct)
    assert Attitude.get_direction() == Direction.OUT
    standard = Attitude(roll=10, pitch=10, yaw=12)
    built = Attitude.get_struct().build(standard)
    assert built == b"\x00\n\x00\n\x00\x0c"
    assert Attitude.get_struct().parse(built) == standard


def test_status_response():
    target_bytes = minus_preamble(messages.attitude_response)
    struct = Attitude.get_struct()
    target_data = struct.parse(target_bytes)
    build_data = Attitude(roll=24578, pitch=43775, yaw=3584)
    # parsed target and manually created dataclass are the same
    assert target_data == build_data
    # Building the manual definition is the same as the parsed target data
    built_bytes = struct.build(build_data)
    assert target_bytes == built_bytes
