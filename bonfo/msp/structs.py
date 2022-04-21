import logging

from construct import Checksum, ChecksumError, IfThenElse, Optional

from bonfo.msp.versions import MSPVersions

logger = logging.getLogger(__name__)


class MSPVersion(IfThenElse):
    def __init__(self, thensubcon, version_added: MSPVersions, elsesubcon=None) -> None:
        self.version_added = version_added
        if elsesubcon is None:
            elsesubcon = Optional(thensubcon)
        super().__init__(self.version_checker, thensubcon, elsesubcon)
        # do we need some way to allow a field to be optional and required in the dataclass init?
        # self.flagbuildnone = elsesubcon.flagbuildnone

    def version_checker(self, context):
        # Get msp version from params context
        msp: MSPVersions = context._params.get("msp", None)
        if msp is not None:
            return msp.value >= self.version_added.value
        return True


class LenientChecksum(Checksum):
    """LenientChecksum doesn't raise an error on checksum failure."""

    def _parse(self, stream, context, path):
        try:
            return super()._parse(stream, context, path)
        except ChecksumError as e:
            logger.error("CRC failed {}", exc_info=e)
            return self.checksumfield._parsereport(stream, context, path)
