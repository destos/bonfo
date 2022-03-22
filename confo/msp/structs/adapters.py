from math import floor

from construct import (
    Adapter,
    Byte,
    Int8ub,
)

from confo.msp.codes import MSP


class RcAdapter(Adapter):
    def _decode(self, obj, context, path):
        # Maybe turn into a dict that keeps the original value
        return round(obj / 100.0, 2)

    def _encode(self, obj, context, path):
        return floor(obj * 100.0)


class MessageTypeAdapter(Adapter):
    def _decode(self, obj, context, path):
        return MSP(obj)

    def _encode(self, obj, context, path):
        return obj.value


MessageType = MessageTypeAdapter(Byte)
RcFloat = RcAdapter(Int8ub)
