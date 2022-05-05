import pytest
from construct import Default, Int16ub, StreamError

from bonfo.msp.structs import MSPCutoff
from bonfo.msp.versions import MSPVersions


def test_mspversion_struct():
    """When only specifying the msp version, missing data errors, older versions are optional."""
    struct = MSPCutoff(Int16ub, MSPVersions.V1_44)
    found = struct.parse(b"\xff\x12")
    assert found == 65298

    with pytest.raises(StreamError):
        struct.parse(b"")

    found = struct.parse(b"", msp=MSPVersions.V1_43)
    assert found is None

    found = struct.build(None, msp=MSPVersions.V1_43)
    assert found == b""


def test_mspversion_struct_else_subcon():
    """When providing a non-optional else subcon, it acts differently."""
    struct = MSPCutoff(Int16ub, MSPVersions.V1_44, Default(Int16ub, 0))
    found = struct.parse(b"\xff\x12")
    assert found == 65298

    with pytest.raises(StreamError):
        struct.parse(b"")

    with pytest.raises(StreamError):
        # We error now if nothing is passed for parsing
        struct.parse(b"", msp=MSPVersions.V1_43)

    found = struct.build(None, msp=MSPVersions.V1_43)
    assert found == b"\x00\x00"
