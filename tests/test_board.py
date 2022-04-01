import logging
import unittest
from multiprocessing.synchronize import BoundedSemaphore

import pytest

from bonfo.board import Board
from bonfo.msp.state import Config

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def init_board_mocks(module_mocker):
    init_serial = module_mocker.patch("bonfo.board.Board._init_serial").stub()
    init_serial.is_open = True
    module_mocker.patch("bonfo.board.Board.connect")


@pytest.mark.usefixtures("init_board_mocks")
class TestBoardInit(unittest.TestCase):
    def test_board_init_values(self) -> None:
        board = Board("/dev/tty-mock")
        self.assertIsInstance(board.conf, Config)
        self.assertIsInstance(board.profile, Board.Profile)
        self.assertEqual(board.serial_trials, 100)
        self.assertIsInstance(board.serial_write_lock, BoundedSemaphore)
        self.assertIsInstance(board.serial_read_lock, BoundedSemaphore)
        board._init_serial.assert_called_once_with("/dev/tty-mock", baudrate=115200)  # type: ignore
        board.connect.assert_not_called()  # type: ignore

    def test_board_context_manager(self) -> None:
        with Board("/dev/tty-mock") as board:
            self.assertEqual(board.serial_trials, 100)
            board.connect.assert_called_once_with(trials=100)

    def test_board_context_manager_trials_changed(self) -> None:
        with Board("/dev/tty-mock", trials=2) as board:
            self.assertEqual(board.serial_trials, 2)
            board.connect.assert_called_once_with(trials=2)
