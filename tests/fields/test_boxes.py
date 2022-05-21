from construct_typed import DataclassStruct

from bonfo.msp.fields.base import Direction
from bonfo.msp.fields.boxes import Boxes, BoxIds


def test_boxids():
    assert isinstance(BoxIds.get_struct(), DataclassStruct)
    assert BoxIds.get_direction() == Direction.OUT
    standard = BoxIds(boxes=Boxes.ARM)
    built = BoxIds.get_struct().build(standard)
    assert built == b"\x00\x00\x00\x00\x00\x00\x00\x01"
    assert BoxIds.get_struct().parse(built) == standard
