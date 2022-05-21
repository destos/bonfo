from functools import reduce
from operator import xor

from construct import (
    Byte,
    Checksum,
    Const,
    Default,
    Enum,
    FixedSized,
    Hex,
    Int8ub,
    Mapping,
    RawCopy,
    Rebuild,
    Struct,
    this,
)

from bonfo.msp.structs import FrameStruct

from .adapters import MessageType
from .codes import frame_map
from .expr import zero_none_len_

# INFO: Make sure all fields are loaded before processing messages
from .fields import *  # noqa

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
        "frame_id" / Mapping(MessageType, frame_map),
        "fields" / FixedSized(this.data_length, FrameStruct(this.frame_id)),  # type:ignore
    )),
    "crc" / Hex(Checksum(
        Byte,
        lambda data: reduce(xor, data, 0),
        this.packet.data
    ))
)
# fmt: on

# The idea for this, if we can't get readline to work
# split the message into the preamble, and data segment.
# We know how long the preamble is, grab until the data length byte
# Use the length to grab the rest + crc value.
# concat the data length byte to newly received bytes and parse the data if available
# Would love to fix StreamReader.readline so I didn't have to do this

MessageTypeEnum = Enum(
    Byte,
    IN=ord(">"),
    OUT=ord("<"),
    ERR=ord("!"),
)

Preamble = Struct(
    "signature" / Const(b"$"),
    "version" / Const(b"M"),
    # Don't need to support v2 at this moment
    # "version" / Default(
    #     Enum(Byte,
    #         V1 = ord("M"),
    #         V2 = ord("X"),
    #     ), "V1"),
    "message_type" / Default(MessageTypeEnum, "IN"),
    "data_length" / Int8ub,
    "frame_id" / Mapping(MessageType, frame_map),
)

Data = Struct(
    "packet"
    / RawCopy(
        Struct(
            "data_length" / Int8ub,
            "frame_id" / Mapping(MessageType, frame_map),
            "fields" / FixedSized(this.data_length, FrameStruct(this.frame_id)),  # type:ignore
        )
    ),
    # "crc" / Byte
    "crc" / Hex(Checksum(Byte, lambda data: reduce(xor, data, 0), this.packet.data)),
)
