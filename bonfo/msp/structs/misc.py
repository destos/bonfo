import logging

from construct import Checksum, ChecksumError

logger = logging.getLogger(__name__)


class LenientChecksum(Checksum):
    """LenientChecksum Don't raise an error on checksum failure."""

    def _parse(self, stream, context, path):
        try:
            return super()._parse(stream, context, path)
        except ChecksumError as e:
            logger.error("CRC failed {}", exc_info=e)
            return self.checksumfield._parsereport(stream, context, path)
