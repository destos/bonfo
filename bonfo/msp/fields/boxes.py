"""Boxes are betaflight feature checkboxes."""

from dataclasses import dataclass

from construct import Int8ub, Int64ub
from construct_typed import FlagsEnumBase, TFlagsEnum, csfield

from ..codes import MSP
from .base import MSPFields
from .utils import BIT

__all__ = ["BoxNames", "BoxIds", "Boxes"]


class Boxes(FlagsEnumBase):
    ARM = BIT(0)  # "ARM",
    ANGLE = BIT(1)  # "ANGLE",
    HORIZON = BIT(2)  # "HORIZON",
    BARO = BIT(3)  # (deprecated) "BARO",
    ANTIGRAVITY = BIT(4)  # "ANTI GRAVITY",
    MAG = BIT(5)  # "MAG",
    HEADFREE = BIT(6)  # "HEADFREE",
    HEADADJ = BIT(7)  # "HEADADJ",
    CAMSTAB = BIT(8)  # "CAMSTAB",
    CAMTRIG = BIT(9)  # (deprecated) "CAMTRIG",
    GPSHOME = BIT(10)  # (deprecated) "GPS HOME",
    GPSHOLD = BIT(11)  # (deprecated) "GPS HOLD",
    PASSTHRU = BIT(12)  # "PASSTHRU",
    BEEPERON = BIT(13)  # "BEEPER",
    LEDMAX = BIT(14)  # (deprecated) "LEDMAX",
    LEDLOW = BIT(15)  # "LEDLOW",
    LLIGHTS = BIT(16)  # (deprecated) "LLIGHTS",
    CALIB = BIT(17)  # "CALIB",
    GOV = BIT(18)  # (deprecated) "GOVERNOR",
    OSD = BIT(19)  # "OSD DISABLE",
    TELEMETRY = BIT(20)  # "TELEMETRY",
    GTUNE = BIT(21)  # (deprecated) "GTUNE",
    RANGEFINDER = BIT(22)  # (deprecated) "RANGEFINDER",
    SERVO1 = BIT(23)  # "SERVO1",
    SERVO2 = BIT(24)  # "SERVO2",
    SERVO3 = BIT(25)  # "SERVO3",
    BLACKBOX = BIT(26)  # "BLACKBOX",
    FAILSAFE = BIT(27)  # "FAILSAFE",
    AIRMODE = BIT(28)  # "AIR MODE",
    THREED = BIT(29)  # "3D DISABLE / SWITCH",
    FPVANGLEMIX = BIT(30)  # "FPV ANGLE MIX",
    BLACKBOXERASE = BIT(31)  # "BLACKBOX ERASE (>30s)",
    CAMERA1 = BIT(32)  # "CAMERA CONTROL 1",
    CAMERA2 = BIT(33)  # "CAMERA CONTROL 2",
    CAMERA3 = BIT(34)  # "CAMERA CONTROL 3",
    FLIPOVERAFTERCRASH = BIT(35)  # "FLIP OVER AFTER CRASH",
    PREARM = BIT(36)  # "PREARM",
    BEEPGPSCOUNT = BIT(37)  # "GPS BEEP SATELLITE COUNT",
    THREEDONASWITCH = BIT(38)  # (deprecated)  "3D ON A SWITCH",
    VTXPITMODE = BIT(39)  # "VTX PIT MODE",
    USER1 = BIT(40)  # "USER1",
    USER2 = BIT(41)  # "USER2",
    USER3 = BIT(42)  # "USER3",
    USER4 = BIT(43)  # "USER4",
    PIDAUDIO = BIT(44)  # "PID AUDIO",
    PARALYZE = BIT(45)  # "PARALYZE",
    GPSRESCUE = BIT(46)  # "GPS RESCUE",
    ACROTRAINER = BIT(47)  # "ACRO TRAINER",
    VTXCONTROLDISABLE = BIT(48)  # "VTX CONTROL DISABLE",
    LAUNCHCONTROL = BIT(49)  # "LAUNCH CONTROL",
    MSPOVERRIDE = BIT(50)  # "MSP OVERRIDE",
    STICKCOMMANDDISABLE = BIT(51)  # "STICK COMMANDS DISABLE",
    BEEPERMUTE = BIT(52)  # "BEEPER MUTE",


@dataclass
class BoxNames(MSPFields, get_code=MSP.BOXNAMES):
    """May not be needed, Boxes enum provides names."""

    temp: int = csfield(Int8ub)


@dataclass
class BoxIds(MSPFields, get_code=MSP.BOXIDS):
    boxes: Boxes = csfield(TFlagsEnum(Int64ub, Boxes))
