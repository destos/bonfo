import functools
import logging
from enum import Enum
from typing import Any, Dict, Optional

from construct_typed import DataclassMixin, DataclassStruct

from bonfo.msp.codes import MSP

logger = logging.getLogger(__name__)


class Direction(Enum):
    """Direction of message from board."""

    IN = 1  # To board
    OUT = 2  # From board
    BOTH = 3  # Bidirectional


class MSPFields(DataclassMixin):
    get_code: Optional[MSP] = None
    set_code: Optional[MSP] = None

    @classmethod
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
def build_fields_mapping() -> Dict[MSP, Optional[DataclassStruct[Any]]]:
    fields_mappings = dict()
    for fields in MSPFields.__subclasses__():
        struct = fields.get_struct()
        if fields.get_code is not None:
            fields_mappings[fields.get_code] = struct
        if fields.set_code is not None:
            fields_mappings[fields.set_code] = struct
    return fields_mappings
