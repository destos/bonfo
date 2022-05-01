from bonfo.msp.codes import MSP
from bonfo.msp.fields.config import SelectPID, SelectRate
from bonfo.msp.message import Message
from bonfo.msp.structs import FrameStruct
from bonfo.msp.utils import msg_packet, out_message_builder


def test_select_setting_ack():
    msg = Message.parse(b"$M>\x00\xd2\xd2")
    msg = msg_packet(msg)
    assert msg.frame_id == MSP.SELECT_SETTING
    assert msg.data_length == 0
    assert msg.fields is None


def test_out_message_builder():
    out_msg = out_message_builder(MSP.SELECT_SETTING, fields=(SelectPID(2)))
    assert out_msg == b'$M<\x01\xd2\x01\xd2'


def test_frame_struct():
    result = FrameStruct(MSP.SELECT_SETTING).build(SelectRate(2))
    assert result == b"\x81"
