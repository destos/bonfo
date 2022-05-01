import arrow
from construct_typed import DataclassStruct

from bonfo.msp.fields.base import Direction
from bonfo.msp.fields.statuses import (
    ApiVersion,
    BoardInfo,
    BuildInfo,
    ConfigurationProblemsFlags,
    FcVariant,
    FcVersion,
    Status,
    StatusEx,
    TargetCapabilitiesFlags,
)
from tests import messages
from tests.utils import minus_preamble


def test_api_version():
    assert isinstance(ApiVersion.get_struct(), DataclassStruct)
    assert ApiVersion.get_direction() == Direction.OUT
    standard = ApiVersion(msp_protocol=0, api_major=1, api_minor=43)
    built = ApiVersion.get_struct().build(standard)
    assert built == b"\x00\x01+"
    assert ApiVersion.get_struct().parse(built) == standard


def test_fc_variant():
    assert isinstance(FcVariant.get_struct(), DataclassStruct)
    assert FcVariant.get_direction() == Direction.OUT
    standard = FcVariant(variant="BTFL")
    built = FcVariant.get_struct().build(standard)
    assert built == b"BTFL"
    assert FcVariant.get_struct().parse(built) == standard


def test_fc_version():
    assert isinstance(FcVersion.get_struct(), DataclassStruct)
    assert FcVersion.get_direction() == Direction.OUT
    standard = FcVersion(major=1, minor=12, patch=21)
    built = FcVersion.get_struct().build(standard)
    assert built == b"\x01\x0c\x15"
    assert FcVersion.get_struct().parse(built) == standard


def test_build_info():
    assert isinstance(BuildInfo.get_struct(), DataclassStruct)
    assert BuildInfo.get_direction() == Direction.OUT
    standard = BuildInfo(date_time=arrow.get(2013, 5, 5, 10, 20, 30), git_hash="85c6fdf")
    built = BuildInfo.get_struct().build(standard)
    assert built == b"May 5 201310:20:30\x0085c6fdf"
    assert BuildInfo.get_struct().parse(built) == standard


def xtest_status_response():
    """Status not used."""
    target_bytes = minus_preamble(messages.status_response)
    built_bytes = Status.get_struct().build(Status(cycle_time=10, i2c_error=10, active_sensors=12, mode=1, profile=2))
    assert target_bytes == built_bytes


def xtest_status_ex_response():
    target_bytes = minus_preamble(messages.ssstatus_ex_response)
    parsed = StatusEx.get_struct().parse(target_bytes)
    assert parsed == dict()
    # built_bytes = StatusEx.get_struct().build(
    #     StatusEx(cycle_time=10, i2c_error=10, active_sensors=dict(), mode=1, pid_profile=2)
    # )
    # assert target_bytes == built_bytes


def test_board_info():
    assert isinstance(BoardInfo.get_struct(), DataclassStruct)
    assert BoardInfo.get_direction() == Direction.OUT
    target_bytes = minus_preamble(messages.board_info)
    struct = BoardInfo.get_struct()
    parsed = struct.parse(target_bytes)
    target = BoardInfo(
        short_name="S405",
        hardware_revision=0,
        uses_max7456=2,
        target_capabilities=TargetCapabilitiesFlags(55),
        target_name="STM32F405",
        board_name="CLRACINGF4",
        manufacturer_id="CLRA",
        signature="",
        mcu_type=3,
        configuration_state=2,
        sample_rate=16415,
        configuration_problems=ConfigurationProblemsFlags(0),
        _target_name_length=9,
        _board_name_length=10,
        _manufacturer_id_length=4,
    )
    assert parsed == target
    assert BoardInfo.build(parsed) == target_bytes
