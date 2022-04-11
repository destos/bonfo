import logging
import unittest
from multiprocessing.synchronize import BoundedSemaphore

import pytest

from bonfo.board import Board, Profile
from bonfo.msp.state import Config

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def init_board_mocks(module_mocker):
    init_serial = module_mocker.patch("bonfo.board.Board._init_serial").stub()
    init_serial.is_open = True
    module_mocker.patch("bonfo.board.Board.connect")


@pytest.fixture(scope="function")
def init_msg_mocks(module_mocker):
    module_mocker.patch("bonfo.board.Board.send_msg").stub()
    module_mocker.patch("bonfo.board.Board.receive_msg").stub()


@pytest.mark.usefixtures("init_board_mocks")
class TestBoardInit(unittest.TestCase):
    def test_board_init_values(self) -> None:
        board = Board("/dev/tty-mock")
        self.assertIsInstance(board.conf, Config)
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


# @pytest.mark.usefixtures("init_board_mocks", "init_msg_mocks")
# class TestBoardProfile(unittest.TestCase):

#     @pytest.fixture(autouse=True)
#     def test_as_property(self, mocker):
#         board = mocker.stub()
#         board.profile = Profile.as_property(board, (1, 6))

#         self.assertEqual(board.profile, 1)


@pytest.mark.usefixtures("init_board_mocks")
class TestBoardProfileManager(unittest.TestCase):
    def test_initial_state(self) -> None:
        board = Board("/dev/tty-mock")
        self.assertIsInstance(board.profile, Profile)
        self.assertEqual(board.profile.pid, 1)
        self.assertEqual(board.profile.rate, 1)
        self.assertFalse(board.profile.revert_on_exit)
        self.assertEqual(board.profile.board, board)

    def xtest_profile_manager_pid_side_effects(self) -> None:
        board = Board("/dev/tty-mock")
        self.assertEqual(board.profile.pid, 1)
        self.assertEqual(board.profile.rate, 1)
        self.assertFalse(board.profile.revert_on_exit)
        with board.profile(pid_profile=3, revert_on_exit=True):
            self.assertEqual(board.profile.pid, 3)
            self.assertEqual(board.profile.rate, 1)
            self.assertTrue(board.profile.revert_on_exit)

    def xtest_profile_manager_connects(self) -> None:
        pass
