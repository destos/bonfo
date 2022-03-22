from copy import copy
from functools import reduce
from operator import xor
from construct import (
    Byte,
    Bytes,
    Checksum,
    Computed,
    Const,
    Default,
    Enum,
    Flag,
    Hex,
    If,
    IfThenElse,
    Int16ub,
    Mapping,
    Optional,
    Pointer,
    Probe,
    RawCopy,
    Rebuild,
    Struct,
    Int8ub,
    Switch,
    Tell,
    len_,
    this,
)

from confo.msp.codes import MSP
from confo.msp.structs.adapters import MessageType
from . import config as structs

# Do this map differently + automate or just register the structs?
# how to handle returns/response from board?
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
}


message_id_mapping = {m.value: m for m in MSP}


# def do_v1_crc(data):
#     # first byte is length
#     data = copy(data)
#     checksum = data[0]
#     for byte in data[1:]:
#         checksum ^= byte
#     return checksum


# fmt: off
# MSP v1 message struct
Message = Struct(
    "signature" / Const(b"$"),
    # "version" / Const(b"M")
    "version" / Default(
        Enum(Byte,
            V1 = ord("M"),
            V2 = ord("X"),
        ), "V1"),
    "message_type" / Default(
        Enum(Byte,
            IN = ord(">"),
            OUT = ord("<"),
            ERR = ord("!"),
        ), "IN"),
    "_is_out" / Computed(this.message_type == "OUT"),
    "_start" / Tell,
    # How to have this computed?
    # "data_length" / IfThenElse(
    #     this._is_out,
    #     Rebuild(Byte, len_(this._packet)),
    #     Byte
    # ),
    "data_length" / Rebuild(Byte, len_(this._packet)),
    "frame_id" / Mapping(MessageType, message_id_mapping),
    # "message_id" / Enum(Byte, MSP)
    # "fields" / ApiVersion
    "fields" / Switch(this.frame_id.value, function_map),
    "_end" / Tell,
    "_packet" / Pointer(this._start, Bytes(this._end - this._start)),

    # "crc" / Checksum(Byte, lambda data: reduce(xor, data, 0), this._packet.data)
    "checksum" / Hex(Checksum(
        Byte,
        # do_v1_crc,
        lambda data: reduce(xor, data, 0),
        this._packet
        # lambda data: do_v1_crc(data), this._packet
        # Computed(this.data_length)
    ))
    # "checksum" / Hex(Checksum(
    #     Byte,
    #     # do_v1_crc,
    #     lambda data: reduce(xor, data, 0),
    #     this._packet
    #     # lambda data: do_v1_crc(data), this._packet
    #     # Computed(this.data_length)
    # ))
    # "crc" / Hex(Checksum(Int8ub, lambda data: novatel_binary_crc(data), this.fields.data))
)
# fmt: on

# TestMessage = Struct(
#     "wat" / Const(b"!"),
#     "length" / Rebuild(Byte, len_(this.items)),
#     "start" / Tell,
#     "items" / Struct(
#         "waka" / Flag,
#         "item" / Int16ub,
#     ),
#     Probe(lookahead=32),
#     "checksum" / Pointer(
#         this.start,
#         Checksum(Byte, lambda data: reduce(xor, data, 0), this.items)
#         # lambda data: do_v1_crc(data), this._packet
#         # Computed(this.data_length)
#     ),
# )


# TestMessage = Struct(
#     "header" / Const(b"4"),
#     "bits" / RawCopy(
#         Default(Int16ub, 0),
#     ),
#     "crc" / Checksum(Byte, lambda data: reduce(xor, data, 0), this.bits.data)
# )

# DIS WORKS YO
TestMessage = Struct(
    "header" / Const(b"4"),
    "_start" / Tell,
    # This may be able to just use start_env
    "data_length" / Rebuild(Byte, len_(this._packet)),
    "bits" / Default(Int16ub, 0),
    "_end" / Tell,
    "_packet" / Pointer(this._start, Bytes(this._end - this._start)),
    "crc" / Checksum(Byte, lambda data: reduce(xor, data, 0), this._packet)
)
