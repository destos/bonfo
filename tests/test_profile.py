from construct import Container
from pytest_mock import MockerFixture

from bonfo.board import Profile
from bonfo.msp.codes import MSP


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


async def xtest_board_ready_wait(mock_board):
    "Board ready event halts profile context manager."
    # Make sure we halt on a future await wait()
    mock_board.ready.clear()
    profile = Profile(board=mock_board)
    async with profile() as pro:
        assert pro.board.ready.is_set() is False


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
    apple_changes_spy = mocker.spy(Profile, "apply_changes")
    profile = Profile(board=mock_board)
    profile.board.send_receive.side_effect = [
        # return from _set_pid_to_board call, not used currently
        (None, None),
        # return from _set_rate_to_board call, not used currently
        (None, None),
        # return from _set_profiles_from_board call, inside apply_changes
        (None, Container(pid_profile=2, rate_profile=4)),
        # second return from _set_pid_to_board call, not used currently
        (None, None),
        # second return from _set_rate_to_board call, not used currently
        (None, None),
        # return from _set_profiles_from_board second call, inside apply_changes
        (None, Container(pid_profile=1, rate_profile=1)),
    ]
    assert profile.pid == 1
    assert profile.rate == 1
    async with profile(pid=2, rate=4, revert_on_exit=True) as pro:
        assert pro._revert_to_profiles == (1, 1)
        assert pro.pid == 2
        assert pro.rate == 4
        assert isinstance(pro, Profile)
        apple_changes_spy.assert_called_once_with(profile)
    # Called once in total after exit
    apple_changes_spy.assert_has_calls([mocker.call(profile), mocker.call(profile)])
    assert profile._revert_to_profiles == (1, 1)
    # pid and rate not reverted
    assert profile.pid == 1
    assert profile.rate == 1
    profile.board.send_receive.assert_any_await(MSP.SELECT_SETTING, dict(pid_profile=2))
    profile.board.send_receive.assert_any_await(MSP.SELECT_SETTING, dict(rate_profile=4))
    profile.board.send_receive.assert_any_await(MSP.STATUS_EX)
    profile.board.send_receive.assert_any_await(MSP.SELECT_SETTING, dict(pid_profile=1))
    profile.board.send_receive.assert_any_await(MSP.SELECT_SETTING, dict(rate_profile=1))
    profile.board.send_receive.assert_any_await(MSP.STATUS_EX)


async def test_set_profiles_from_board(mock_board):
    "Sync down the current board profiles and set to local attributes."
    profile = Profile(board=mock_board)
    profile.board.send_receive.side_effect = [
        (None, Container(pid_profile=3, rate_profile=6)),
    ]
    assert profile.pid == 1
    assert profile.rate == 1
    result = await profile._set_profiles_from_board()
    profile.board.send_receive.assert_any_await(MSP.STATUS_EX)
    assert profile._profile_tracker == (3, 6) == result
    assert profile._state == Profile.SyncedState.CLEAN
    assert profile.pid == 3
    assert profile.rate == 6


async def test_send_pid_to_board(mock_board):
    "Send the selected PID to the board, should not change local values."
    profile = Profile(board=mock_board)
    profile.board.send_receive.side_effect = [
        (None, None),
    ]
    assert profile.pid == 1
    await profile._send_pid_to_board(3)
    profile.board.send_receive.assert_any_await(MSP.SELECT_SETTING, dict(pid_profile=3))
    assert profile._profile_tracker == (1, 1)
    assert profile._state == Profile.SyncedState.UNFETCHED
    assert profile.pid == 1


async def test_send_rate_to_board(mock_board):
    "Send the selected rate to the board, should not change local values."
    profile = Profile(board=mock_board)
    profile.board.send_receive.side_effect = [
        (None, None),
    ]
    assert profile.rate == 1
    await profile._send_rate_to_board(3)
    profile.board.send_receive.assert_any_await(MSP.SELECT_SETTING, dict(rate_profile=3))
    assert profile._profile_tracker == (1, 1)
    assert profile._state == Profile.SyncedState.UNFETCHED
    assert profile.rate == 1


async def test_apply_changes_applied(mock_board, mocker: MockerFixture):
    "Full apply test."
    mock_send_pid = mocker.patch("bonfo.board.Profile._send_pid_to_board")
    mock_send_rate = mocker.patch("bonfo.board.Profile._send_rate_to_board")
    mock_set_profiles = mocker.patch.object(Profile, "_set_profiles_from_board", return_value=(2, 2))
    profile = Profile(board=mock_board)
    profile._state = Profile.SyncedState.AWAITING_APPLY
    profile._profile_tracker = (2, 2)
    result = await profile.apply_changes()
    assert profile._profile_tracker == (2, 2)
    assert result is True
    mock_send_pid.assert_awaited_once_with(2)
    mock_send_rate.assert_awaited_once_with(2)
    mock_set_profiles.assert_awaited_once_with()


async def test_apply_changes_bad_state(mock_board, mocker: MockerFixture):
    "Profile is in bad state to apply"
    mock_send_pid = mocker.patch("bonfo.board.Profile._send_pid_to_board")
    mock_send_rate = mocker.patch("bonfo.board.Profile._send_rate_to_board")
    mock_set_profiles = mocker.patch.object(Profile, "_set_profiles_from_board", return_value=(2, 2))
    profile = Profile(board=mock_board)
    profile._state = Profile.SyncedState.CLEAN
    profile._profile_tracker = (2, 2)
    result = await profile.apply_changes()
    assert profile._profile_tracker == (2, 2)
    # no need to apply, so returns False
    assert result is False
    mock_send_pid.assert_not_awaited()
    mock_send_rate.assert_not_awaited()
    mock_set_profiles.assert_not_awaited()


async def test_apply_changes_different_board_result(mock_board, mocker: MockerFixture):
    "Profiles from board differ"
    mock_send_pid = mocker.patch("bonfo.board.Profile._send_pid_to_board")
    mock_send_rate = mocker.patch("bonfo.board.Profile._send_rate_to_board")
    mock_set_profiles = mocker.patch.object(Profile, "_set_profiles_from_board", return_value=(2, 4))
    profile = Profile(board=mock_board)
    profile._state = Profile.SyncedState.AWAITING_APPLY
    profile._profile_tracker = (2, 2)
    result = await profile.apply_changes()
    assert profile._profile_tracker == (2, 2)
    # no need to apply, so returns False
    assert result is False
    mock_send_pid.assert_awaited_once_with(2)
    mock_send_rate.assert_awaited_once_with(2)
    mock_set_profiles.assert_awaited_once_with()
