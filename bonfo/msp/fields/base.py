import functools
import logging
from enum import Enum
from typing import Dict, Optional

from construct_typed import DataclassMixin, DataclassStruct

from bonfo.msp.codes import MSP

logger = logging.getLogger(__name__)

translator_map: Dict[MSP, "MSPFields"] = dict()


class Direction(Enum):
    """Direction of message from board."""

    IN = 1  # To board
    OUT = 2  # From board
    BOTH = 3  # Bidirectional


class MSPFields(DataclassMixin):
    get_code: Optional[MSP] = None
    set_code: Optional[MSP] = None

    def __init_subclass__(cls, get_code: MSP = None, set_code: MSP = None) -> None:
        cls.get_code = get_code
        cls.set_code = set_code

    @classmethod
    @functools.cache
    def get_struct(cls) -> Optional[DataclassStruct]:
        """Returns the generated DataClassStruct based on the configuration of this MSPFields subclass.

        Returns:
            Optional[DataclassStruct]: The Struct used for parsing or building MSP message data
        """
        try:
            struct = DataclassStruct(cls)
        except TypeError as e:
            logger.exception("Error building struct from dataclass", exc_info=e)
            return None
        return struct

    def build(self):
        return self.get_struct().build(self)

    @classmethod
    @functools.cache
    def get_direction(cls) -> Optional[Direction]:
        if cls.get_code is not None and cls.set_code is not None:
            return Direction.BOTH
        if cls.get_code is None:
            return Direction.IN
        if cls.set_code is None:
            return Direction.OUT
        return None


@functools.cache
def build_translator_map():
    if len(translator_map) > 0:
        return translator_map
    for fields in MSPFields.__subclasses__():
        struct = fields.get_struct()
        if fields.get_code is not None:
            translator_map[fields.get_code] = struct
        if fields.set_code is not None:
            translator_map[fields.set_code] = struct
    return translator_map


@functools.cache
def get_struct(get_code: MSP) -> Optional[DataclassStruct]:
    return build_translator_map()[get_code]


@functools.cache
def set_struct(set_code: MSP) -> Optional[DataclassStruct]:
    return build_translator_map()[set_code]
