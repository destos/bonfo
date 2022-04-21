from enum import Enum

from semver import VersionInfo

parse = VersionInfo.parse


class MSPVersions(Enum):
    V1_40 = parse("1.40.0")
    V1_41 = parse("1.41.0")
    V1_42 = parse("1.42.0")
    V1_43 = parse("1.43.0")
    V1_44 = parse("1.44.0")
