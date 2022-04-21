import asyncio

import pytest
from pytest_mock import MockerFixture, MockFixture


@pytest.fixture(scope="function")
def init_board_mocks(module_mocker):
    init_serial = module_mocker.patch("bonfo.board.Board._init_serial").stub()
    init_serial.is_open = True
    module_mocker.patch("bonfo.board.Board.connect")



@pytest.fixture(scope="function")
def mock_open_serial_connection(module_mocker, mocker):
    read = mocker.AsyncMock()
    reader = mocker.Mock(read=read)
    write = mocker.AsyncMock()
    writer = mocker.Mock(write=write)
    open_serial = module_mocker.patch("bonfo.board.open_serial_connection")
    open_serial.side_effect = [(reader, writer)]
    return open_serial


@pytest.fixture(scope="function")
def mock_send_receive(module_mocker):
    return module_mocker.patch("bonfo.board.Board.send_receive")


@pytest.fixture(scope="function")
def mock_profile(module_mocker, mocker: MockerFixture):
    profile = module_mocker.patch("bonfo.board.Profile")
    profile.pid = 2
    profile.rate = 2
    profile._check_connection = mocker.AsyncMock()
    return profile


@pytest.fixture(scope="function")
def mock_board(mocker: MockerFixture) -> MockFixture:
    board = mocker.Mock().stub()
    board.ready = asyncio.Event()
    # Always ready
    board.ready.set()
    board.send_receive = mocker.AsyncMock()
    return board
