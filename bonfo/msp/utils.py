import logging

from construct import Debugger

from .codes import MSP
from .message import Message

logger = logging.getLogger(__name__)


def message_builder(message_type: str, code: MSP, fields=None, debug=False):
    Msg = Debugger(Message) if debug else Message
    return Msg.build(  # type: ignore
        dict(message_type=message_type, packet=dict(value=dict(frame_id=code, fields=fields)))
    )


def out_message_builder(code: MSP, fields=None, debug=False):
    return message_builder("OUT", code, fields, debug=debug)


def in_message_builder(code: MSP, fields=None, debug=False):
    return message_builder("IN", code, fields, debug=debug)
