from construct_typed import DataclassStruct

from bonfo.msp.fields.base import Direction
from bonfo.msp.fields.boxes import BoxIds


def test_boxids():
    assert isinstance(BoxIds.get_struct(), DataclassStruct)
    assert BoxIds.get_direction() == Direction.OUT
    standard = BoxIds()
    built = BoxIds.get_struct().build(standard)
    assert built == b""
    assert BoxIds.get_struct().parse(built) == standard
