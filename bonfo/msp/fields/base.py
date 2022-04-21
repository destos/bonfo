import functools
from enum import Enum

from construct_typed import DataclassMixin, DataclassStruct

from bonfo.msp.codes import MSP

translator_map = dict()


class Direction(Enum):
    """Direction of message from board."""

    IN = 1  # To board
    OUT = 2  # From board
    BOTH = 3  # Bidirectional


class MSPFields(DataclassMixin):
    def __init_subclass__(cls, get_code: MSP = None, set_code: MSP = None) -> None:
        cls.get_code = get_code
        cls.set_code = set_code
        super().__init_subclass__()

    @classmethod
    @property
    @functools.cache
    def struct(cls) -> DataclassStruct:
        struct = DataclassStruct(cls)
        # This shouldn't be here
        if cls.get_code is not None:
            translator_map[cls.get_code] = struct
        if cls.set_code is not None:
            translator_map[cls.set_code] = struct
        return struct

    @classmethod
    @property
    @functools.cache
    def direction(cls) -> Direction:
        if cls.get_code is not None and cls.set_code is not None:
            return Direction.BOTH
        if cls.get_code is None:
            return Direction.IN
        if cls.set_code is None:
            return Direction.OUT
