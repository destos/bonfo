import logging
from functools import reduce
from operator import xor

from construct import (
    Byte,
    Checksum,
    ChecksumError,
    Const,
    Default,
    Enum,
    FixedSized,
    FuncPath,
    Hex,
    Mapping,
    Optional,
    RawCopy,
    Rebuild,
    Struct,
    Switch,
    this,
)

from bonfo.msp.codes import MSP
from bonfo.msp.structs.adapters import MessageType

from .structs import config as structs

logger = logging.getLogger(__name__)

# Do this map differently + automate or just register the structs?
function_map = {
    MSP.API_VERSION: structs.ApiVersion,
    MSP.FC_VARIANT: structs.FcVariant,
    MSP.FC_VERSION: structs.FcVersion,
    MSP.BUILD_INFO: structs.BuildInfo,
    MSP.BOARD_INFO: structs.BoardInfo,
    MSP.UID: structs.Uid,
    MSP.ACC_TRIM: structs.AccTrim,
    MSP.NAME: structs.Name,
    MSP.STATUS: structs.Status,
    MSP.STATUS_EX: structs.StatusEx,
    MSP.RX_CONFIG: structs.RxConfig,
    MSP.RC_TUNING: structs.RcTuning,
    MSP.RAW_IMU: structs.RawIMU,
}


message_id_mapping = {m.value: m for m in MSP}


def zero_none_len(data):
    if data is None:
        return 0
    return len(data)


zero_none_len_ = FuncPath(zero_none_len)  # type: ignore


class LenientChecksum(Checksum):
    def _parse(self, stream, context, path):
        try:
            return super()._parse(stream, context, path)
        except ChecksumError as e:
            logger.error("CRC failed {}", exc_info=e)
            return self.checksumfield._parsereport(stream, context, path)


# fmt: off
# MSP v1 message struct
Message = Struct(
    "signature" / Const(b"$"),
    "version" / Const(b"M"),
    # Don't need to support v2 at this moment
    # "version" / Default(
    #     Enum(Byte,
    #         V1 = ord("M"),
    #         V2 = ord("X"),
    #     ), "V1"),
    "message_type" / Default(Enum(
        Byte,
        IN = ord(">"),
        OUT = ord("<"),
        ERR = ord("!"),
    ), "IN"),
    # "_is_out" / Computed(this.message_type == "OUT"),
    "packet" / RawCopy(Struct(
        "data_length" / Rebuild(Byte, zero_none_len_(this.fields)),
        "frame_id" / Mapping(MessageType, message_id_mapping),
        "fields" / FixedSized(this.data_length, Optional(Switch(this.frame_id, function_map))),  # type: ignore
    )),
    "crc" / Hex(Checksum(
        Byte,
        lambda data: reduce(xor, data, 0),
        this.packet.data
    ))
)
# fmt: on
