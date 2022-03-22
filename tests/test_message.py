import logging
# from confo.msp.structs.message import Message
from construct import Debugger
from confo.msp.structs.message import TestMessage

from confo.msp.codes import MSP

logger = logging.getLogger(__name__)


# def message_builder(code: MSP, data=dict()):
#     return Message.build(dict(header=dict(frame_id=code, message_type="OUT"), fields=data))


# def xtest_build_basic_message():
#     buff = message_builder(MSP.FC_VERSION)
#     assert buff == b"$M<\x03"

# def test_

def test_message_crc():
    # bits = TestMessage.build(dict(items=dict(item=1234, waka=False)))
    # bits = TestMessage.build(dict(fields=dict(value="123")))
    # bits = Debugger(TestMessage.build(dict(bits=dict(value=252))))
    # msg = TestMessage.parse(b"4x\03\x01\x01\x78")
    # b_msg = TestMessage.build(obj=dict(bits=257))
    # msg = TestMessage.parse(b"4x\01\x01\x00")
    msg = TestMessage.parse(b"4\x01\x01\x78")
    assert msg.bits == 257
    logger.info(msg)
    breakpoint()
    msg = TestMessage.parse(b"4x\x02\x01\x7b")
    assert msg.bits == 513
    logger.info(msg)

    # msg = TestMessage.parse(b"4x\03\x01\x01\x00")
    # assert msg.bits == 257
    # msg = TestMessage.parse(b"4x\03\x02\x01\x03")
    # assert msg.bits == 513
    # b"\x12\x15"
    # assert bits == b"\x04\xd2\xd6"
