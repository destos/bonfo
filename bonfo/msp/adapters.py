from math import floor

import arrow
from construct import Adapter, Array, Byte, ExprAdapter, Int8ub, Int16ub, PaddedString, Validator, obj_

from bonfo.msp.codes import MSP


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
RawSingle = Array(3, Int16ub)

Int8ubPlusOne = ExprAdapter(Int8ub, obj_ + 1, obj_ - 1)

RATEPROFILE_MASK = 0x80  # 1 << 7


class PIDProfileValidator(Validator):
    def _validate(self, obj, context, path):
        return int(obj) in list(range(1, 4))


class RateProfileValidator(Validator):
    def _validate(self, obj, context, path):
        return int(obj) in list(range(1, 7))


SelectPIDProfile = PIDProfileValidator(Int8ubPlusOne)


SelectRateProfile = RateProfileValidator(
    ExprAdapter(
        Int8ub,
        # decoder
        (obj_ + 1) ^ RATEPROFILE_MASK,
        # encoder
        (obj_ ^ RATEPROFILE_MASK) - 1,
    )
)


DATE_TIME_LENGTH = 11 + 8
GIT_HASH_LENGTH = 7


class TimestampAdapter(Adapter):
    def _decode(self, obj, context, path) -> arrow.Arrow:
        try:
            return arrow.get(obj, "MMM  D YYYYHH:mm:ss")
        except arrow.ParserError:
            return arrow.get(obj, "MMM D YYYYHH:mm:ss")

    def _encode(self, obj, context, path) -> str:
        return arrow.get(obj).format("MMM D YYYYHH:mm:ss")


BTFLTimestamp = TimestampAdapter(PaddedString(DATE_TIME_LENGTH, "utf8"))

GitHash = PaddedString(GIT_HASH_LENGTH, "utf8")
