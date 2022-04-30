import asyncio
import logging

from serial_asyncio import serial

from bonfo.board import Board, Profile
from bonfo.msp.fields import BoardInfo

logger = logging.getLogger(__name__)


async def xtest_board_init_values(mock_open_serial_connection, mock_send_receive) -> None:
    board = Board("/dev/tty-mock")
    await board.ready.wait()
    mock_send_receive.side_effect = [(None, None)]
    mock_open_serial_connection.assert_waited_once_with(
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
    assert isinstance(board.info, BoardInfo)
    assert isinstance(board.profile, Profile)
    assert board.serial_trials == 100
    assert isinstance(board.write_lock, asyncio.Event)
    assert isinstance(board.read_lock, asyncio.Event)
    # board._init_serial.assert_called_once_with("/dev/tty-mock", baudrate=115200)  # type: ignore
    # board.connect.assert_not_called()  # type: ignore


def xtest_board_context_manager(self) -> None:
    with Board("/dev/tty-mock").connect() as board:
        assert board.serial_trials == 100
        board.connect.assert_called_once_with(trials=100)


def xtest_board_context_manager_trials_changed(self) -> None:
    with Board("/dev/tty-mock", serial_trails=2).connect() as board:
        assert board.serial_trials == 2
        board.connect.assert_called_once_with(serial_trails=2)


async def xtest_board_connect(mock_open_serial_connection, mock_send_receive):
    mock_send_receive.return_value = (None, None)
    async with Board("/dev/tty").connect() as board:
        assert board.connected.is_set() is True
        assert board.ready.is_set() is True
