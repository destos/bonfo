from enum import Enum

from semver import VersionInfo

parse = VersionInfo.parse


class MSPVersions(Enum):
    V1_40 = parse("0.1.40")
    V1_41 = parse("0.1.41")
    V1_42 = parse("0.1.42")
    V1_43 = parse("0.1.43")
    V1_44 = parse("0.1.44")


MSPMaxSupported = MSPVersions.V1_44
