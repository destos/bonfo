from dataclasses import dataclass

from construct import Int16ub
from construct_typed import csfield

from ..codes import MSP
from .base import MSPFields

__all__ = ["Attitude"]


@dataclass
class Attitude(MSPFields, get_code=MSP.ATTITUDE):
    roll: int = csfield(Int16ub)
    pitch: int = csfield(Int16ub)
    yaw: int = csfield(Int16ub)
