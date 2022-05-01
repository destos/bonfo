import asyncio
import logging

from pytest_mock import MockerFixture
from serial_asyncio import serial

from bonfo.board import Board
from bonfo.msp.fields.statuses import (
    ApiVersion,
    BoardInfo,
    BuildInfo,
    CombinedBoardInfo,
    FcVariant,
    FcVersion,
    Name,
    Uid,
)

logger = logging.getLogger(__name__)


async def test_board_init_values(mock_open_serial_connection, mock_profile, mock_board_get) -> None:
    board = Board("/dev/tty-mock", initial_data=False, profile=mock_profile)
    await board.ready.wait()
    mock_board_get.side_effect = [(None, None)]
    mock_open_serial_connection.assert_awaited_once_with(
        url="/dev/tty-mock",
        baudrate=115200,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=0.1,
        xonxoff=False,
        rtscts=False,
        dsrdtr=False,
    )
    assert board.device == "/dev/tty-mock"
    assert board.baudrate == 115200
    assert isinstance(board.info, CombinedBoardInfo)
    assert board.profile == mock_profile
    assert isinstance(board.write_lock, asyncio.Lock)
    assert isinstance(board.read_lock, asyncio.Lock)
    assert isinstance(board.message_lock, asyncio.Lock)
    mock_profile._check_connection.assert_awaited_once()


async def test_board_connect_manager(mock_open_serial_connection, mock_profile, mock_board_get, mock_board_set):
    mock_board_get.side_effect = [(None, None)]
    async with Board("/dev/tty", initial_data=False).connect() as board:
        assert board.connected.is_set() is True
        assert board.ready.is_set() is True
    assert board.connected.is_set() is False


async def test_board_initial_data_true(
    mock_open_serial_connection, mock_profile, mock_board_get, mocker: MockerFixture
):
    gbi = mocker.patch("bonfo.board.Board.get_board_info")
    async with Board("/dev/tty", initial_data=True, profile=mock_profile).connect() as board:
        gbi.assert_awaited_with()


async def test_board_get_board_info(mock_open_serial_connection, mock_profile, mock_board_get, mocker: MockerFixture):
    cbi = mocker.patch("bonfo.board.CombinedBoardInfo")
    mock_board_get.side_effect = [
        (None, "name"),
        (None, "api"),
        (None, "version"),
        (None, "build_info"),
        (None, "board_info"),
        (None, "variant"),
        (None, "uid"),
    ]
    board = Board("/dev/tty", initial_data=False, profile=mock_profile)
    # does not run on init
    mock_board_get.assert_not_awaited()
    board.connected.set()
    # TODO: test for returned mocked info
    await board.get_board_info()
    mock_board_get.assert_has_awaits(
        [
            mocker.call(Name),
            mocker.call(ApiVersion),
            mocker.call(FcVersion),
            mocker.call(BuildInfo),
            mocker.call(BoardInfo),
            mocker.call(FcVariant),
            mocker.call(Uid),
        ]
    )
    cbi.assert_called_with("name", "api", "version", "build_info", "board_info", "variant", "uid")
