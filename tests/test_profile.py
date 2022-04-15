from construct import Container
from pytest_mock import MockerFixture
from bonfo.board import Profile
from bonfo.msp.codes import MSP
from bonfo.msp.structs.status import StatusEx


def test_profile_str(mock_board) -> None:
    "String cast of profile object."
    profile = Profile(board=mock_board)
    profile._pid = 2
    profile._rate = 3
    assert str(profile) == "pid: 2 rate: 3 SyncedState.UNFETCHED"


def test_profile_pid_attr(mock_board) -> None:
    "Side effects of changing the pid profile via its attribute."
    profile = Profile(board=mock_board)
    assert profile.pid == 1
    assert profile._state == Profile.SyncedState.UNFETCHED
    assert profile._profile_tracker == (1, 1)
    profile.pid = 2
    assert profile.pid == 1
    assert profile._state == Profile.SyncedState.AWAITING_APPLY
    assert profile._profile_tracker == (2, 1)


def test_profile_rate_attr(mock_board) -> None:
    "Side effects of changing the rate profile via its attribute."
    profile = Profile(board=mock_board)
    assert profile.rate == 1
    assert profile._state == Profile.SyncedState.UNFETCHED
    assert profile._profile_tracker == (1, 1)
    profile.rate = 2
    assert profile.rate == 1
    assert profile._state == Profile.SyncedState.AWAITING_APPLY
    assert profile._profile_tracker == (1, 2)


async def test_board_ready_wait():
    "Board ready event halts profile context manager."
    pass


async def test_profile_manager_with_no_args(mock_board, mocker: MockerFixture) -> None:
    "If a profile context manager is made with no args do nothing."
    apple_changes_spy = mocker.spy(Profile, "apply_changes")
    profile = Profile(board=mock_board)
    profile.board.send_receive.side_effect = []
    assert profile.pid == 1
    assert profile.rate == 1
    async with profile() as pro:
        assert pro._revert_to_profiles == (1, 1)
        assert pro.pid == 1
        assert pro.rate == 1
        assert isinstance(pro, Profile)
        apple_changes_spy.assert_called_once_with(profile)
    # Called once in total after exit
    apple_changes_spy.assert_has_calls([mocker.call(profile)])
    assert profile._revert_to_profiles == (1, 1)
    assert profile.pid == 1
    assert profile.rate == 1
    profile.board.send_receive.assert_not_awaited()


async def test_profile_manager_with_selections(mock_board, mocker: MockerFixture) -> None:
    "Side effects of providing a different pid and rate in the async profile manager"
    apple_changes_spy = mocker.spy(Profile, "apply_changes")
    profile = Profile(board=mock_board)
    profile.board.send_receive.side_effect = [
        # return from _set_pid_to_board call, not used currently
        (None, None),
        # return from _set_rate_to_board call, not used currently
        (None, None),
        # return from _set_profiles_from_board call, from the "board"
        (None, Container(pid_profile=2, rate_profile=4)),
    ]
    assert profile.pid == 1
    assert profile.rate == 1
    async with profile(pid=2, rate=4) as pro:
        assert pro._revert_to_profiles == (1, 1)
        assert pro.pid == 2
        assert pro.rate == 4
        assert isinstance(pro, Profile)
        apple_changes_spy.assert_called_once_with(profile)
    # Called once in total after exit
    apple_changes_spy.assert_called_once_with(profile)
    assert profile._revert_to_profiles == (1, 1)
    # pid and rate not reverted
    assert profile.pid == 2
    assert profile.rate == 4
    profile.board.send_receive.assert_any_await(MSP.SELECT_SETTING, dict(pid_profile=2))
    profile.board.send_receive.assert_any_await(MSP.SELECT_SETTING, dict(rate_profile=4))
    profile.board.send_receive.assert_any_await(MSP.STATUS_EX)


async def test_profile_manager_with_revert_on_exit(mock_board, mocker: MockerFixture) -> None:
    "revert_on_exit flag reverts to previous profiles on exit of manager."
    # TODO: fix like others
    mock_apply_changes = mocker.patch("bonfo.board.Profile.apply_changes")
    profile = Profile(board=mock_board)
    assert profile.pid == 1
    assert profile.rate == 1
    async with profile(revert_on_exit=True) as pro:
        assert pro._revert_to_profiles == (1, 1)
        assert pro.pid == 1
        assert pro.rate == 1
        assert isinstance(pro, Profile)
        mock_apply_changes.assert_called_once_with()
    # Called twice in total
    mock_apply_changes.assert_has_calls([mocker.call(), mocker.call()])
    assert profile._revert_to_profiles == (1, 1)
    assert profile.pid == 1
    assert profile.rate == 1
