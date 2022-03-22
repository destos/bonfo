# from .msp.state import Message

# fc_version_response = b"$M>\x03\x01\x00\x01\x15\x16"
# fc_version = Message.parse(fc_version_response)
# print(fc_version)

# fc_variant_response = b"$M>\x04\x02BTFL\x1a"
# fc_variant = Message.parse(fc_variant_response)
# print(fc_variant)

from confo.msp.codes import MSP
from .msp.board import Board

dev = "/dev/tty.usbmodem0x80000001"
with Board(dev) as fc:
    # try:
    sent = fc.send_msg(MSP.FC_VERSION)
    print(sent)
    print(fc.receive_msg())
    # except
