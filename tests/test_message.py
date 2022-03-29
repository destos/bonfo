import logging

# from confo.msp.structs.message import Message
from construct import Debugger
from confo.msp.structs.message import Message, in_message_builder, out_message_builder
from rich import print

from confo.msp.codes import MSP

logger = logging.getLogger(__name__)

# from .msp.state import Message

# fc_version_response = b"$M>\x03\x01\x00\x01\x15\x16"
# fc_version = Message.parse(fc_version_response)
# print(fc_version)

# fc_variant_response = b"$M>\x04\x02BTFL\x1a"
# fc_variant = Message.parse(fc_variant_response)
# print(fc_variant)

def test_build_fc_version_msg():
    buff = in_message_builder(MSP.FC_VERSION, fields=dict(major=1, minor=12, patch=21))
    assert buff == b"$M>\x03\x03\x01\x0c\x15\x18"

# def test_fc_version_msg():
#     buff = Message.parse("$M<\x01\x03\x01\x0c\x15\x1a")
#     # MSP.FC_VERSION, fields=dict(major=1, minor=12, patch=21)

def test_request_fc_version_msg():
    buff = out_message_builder(MSP.FC_VERSION)
    assert buff == b"$M<\x00\x03\x03"


def test_parse_api_version_msg():
    fc_version_response = b"$M>\x03\x01\x00\x01\x15\x16"
    msg = Message.parse(fc_version_response)
    packet = msg.packet.value
    assert msg.crc == 22
    assert msg.message_type == "IN"
    assert packet.frame_id == MSP.API_VERSION
    assert packet.fields == dict(msp_protocol=0, api_major=1, api_minor=21)


# def test_build_fc_variant():
#     buff = message_builder(MSP.FC_VARIANT, fields=dict(name="DAMN"))
#     assert buff == b"$M<\x01\x02\x04DAMN\x01"

def test_fc_variant_request():
    proper_request = b'$M<\x00\x02\x02'
    msg = out_message_builder(MSP.FC_VARIANT, fields=None)
    assert msg == proper_request

def test_fc_variant_response():
    fc_response = b"$M>\x04\x02BTFL\x1a"
    msg = Message.parse(fc_response)
    assert msg.packet.value.fields.name == "BTFL"


# TODO: make sure these messages are correct
def xtest_status_response():
    fc_response = b"$M>\x16e}\x00\x00\x00!\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x00\x1a\x04\x01\x01\x00\x004"

    msg = Message.parse(fc_response)
    values = msg.packet.value.fields
    assert values is None

def test_status_ex_response():
    fc_response = b"$M>\x16\x96}\x00\x00\x00!\x00\x00\x00\x00\x00\x00\x05\x00\x03\x00\x00\x1a\x04\x01\x01\x00\x00\xc4"

    msg = Message.parse(fc_response)
    # TODO: better tests
    assert msg is not None
