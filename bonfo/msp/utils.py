import logging

from construct import Debugger

from .codes import MSP
from .message import Message

logger = logging.getLogger(__name__)


def message_builder(message_type: str, code: MSP, fields=None, debug=False, **context):
    Msg = Debugger(Message) if debug else Message
    return Msg.build(  # type: ignore
        dict(message_type=message_type, packet=dict(value=dict(frame_id=code, fields=fields)), **context)
    )


def out_message_builder(code: MSP, fields=None, debug=False, **context):
    return message_builder("OUT", code, fields, debug=debug, **context)


def in_message_builder(code: MSP, fields=None, debug=False, **context):
    return message_builder("IN", code, fields, debug=debug, **context)


def msg_packet(msg):
    return msg.packet.value


def msg_data(msg):
    try:
        return msg.packet.value.fields
    except Exception as e:
        logger.exception("problem in msg_data", exc_info=e)
        return None
