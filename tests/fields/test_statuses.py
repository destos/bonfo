import arrow
from construct_typed import DataclassStruct

from bonfo.msp.fields.base import Direction
from bonfo.msp.fields.statuses import ApiVersion, BuildInfo, FcVariant, FcVersion, Status, StatusEx
from tests.messages import status_response
from tests.utils import minus_preamble


def test_api_version():
    assert isinstance(ApiVersion.struct, DataclassStruct)
    assert ApiVersion.direction == Direction.OUT
    standard = ApiVersion(msp_protocol=0, api_major=1, api_minor=43)
    built = ApiVersion.struct.build(standard)
    assert built == b"\x00\x01+"
    assert ApiVersion.struct.parse(built) == standard


def test_fc_variant():
    assert isinstance(FcVariant.struct, DataclassStruct)
    assert FcVariant.direction == Direction.OUT
    standard = FcVariant(variant="BTFL")
    built = FcVariant.struct.build(standard)
    assert built == b"BTFL"
    assert FcVariant.struct.parse(built) == standard


def test_fc_version():
    assert isinstance(FcVersion.struct, DataclassStruct)
    assert FcVersion.direction == Direction.OUT
    standard = FcVersion(major=1, minor=12, patch=21)
    built = FcVersion.struct.build(standard)
    assert built == b"\x01\x0c\x15"
    assert FcVersion.struct.parse(built) == standard


def test_build_info():
    assert isinstance(BuildInfo.struct, DataclassStruct)
    assert BuildInfo.direction == Direction.OUT
    standard = BuildInfo(date_time=arrow.get(2013, 5, 5, 10, 20, 30), git_hash="85c6fdf")
    built = BuildInfo.struct.build(standard)
    assert built == b"May 5 201310:20:30\x0085c6fdf"
    assert BuildInfo.struct.parse(built) == standard


def xtest_status_response():
    target_bytes = minus_preamble(status_response)
    built_bytes = Status.struct.build(Status(cycle_time=10, i2c_error=10, active_sensors=12, mode=1, profile=2))
    assert target_bytes == built_bytes


def xtest_status_ex_response():
    target_bytes = minus_preamble(status_response)
    built_bytes = StatusEx.struct.build(
        StatusEx(cycle_time=10, i2c_error=10, active_sensors=dict(), mode=1, pid_profile=2)
    )
    assert target_bytes == built_bytes
