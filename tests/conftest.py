import pytest
from pytest_mock import MockFixture, MockerFixture


@pytest.fixture(scope="function")
def mock_open_serial_connection(module_mocker, mocker):
    read = mocker.AsyncMock()
    reader = mocker.Mock(read=read)
    write = mocker.AsyncMock()
    writer = mocker.Mock(write=write)
    open_conn = module_mocker.patch("bonfo.board.open_serial_connection").return_value = (reader, writer)
    return open_conn


@pytest.fixture(scope="function")
def mock_send_receive(module_mocker, mocker):
    return module_mocker.patch("bonfo.board.Board.send_receive")


@pytest.fixture(scope="function")
def mock_profile(module_mocker):
    pass


@pytest.fixture(scope="function")
def mock_board(mocker: MockerFixture) -> MockFixture:
    board = mocker.Mock().stub()
    board.ready = asyncio.Event()
    # Always ready
    board.ready.set()
    board.send_receive = mocker.AsyncMock()
    return board
