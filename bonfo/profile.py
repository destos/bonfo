"""Profile package for Bonfo."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, AsyncIterator, Optional, Tuple

from .msp.fields.config import SelectPID, SelectRate
from .msp.fields.statuses import StatusEx

if TYPE_CHECKING:
    from .board import Board

logger = logging.getLogger(__name__)


__all__ = ["Profile"]


@dataclass
class Profile:
    """Profile context manager.

    pid and rate properties should always reflect what is currently selected on the board.

    When dealing with internal profile tuples, the order will always be (pid, rate).
    """

    board: "Board"
    # pid: int = 1
    # rate: int = 1
    # pid: Annotated[int, field(default=1)]
    # rate: Annotated[int, field(default=1)]

    # pid: int
    # rate: int
    # TODO: move to property classes that have individual synced states and setters
    _pid: int = field(default=1, init=False, repr=False)
    _rate: int = field(default=1, init=False, repr=False)

    # Track profile changes before they are applied
    _profile_tracker: Tuple[int, int] = field(default_factory=lambda: (1, 1), repr=False)

    # hold previous profiles for reversion purposes
    _revert_to_profiles: Tuple[int, int] = field(default_factory=lambda: (1, 1), repr=False)

    class SyncedState(Enum):
        """Local synced/saved status for selected profiles."""

        UNFETCHED = 1
        FETCHING = 2
        CLEAN = 3
        AWAITING_APPLY = 4

    _state = SyncedState.UNFETCHED

    def __str__(self) -> str:
        return f"pid: {self.pid} rate: {self.rate} {self._state}"

    @property
    def pid(self) -> int:
        if self._state == self.SyncedState.UNFETCHED:
            logger.warning("PID profile not yet fetched from board")
        return self._pid

    @pid.setter
    def pid(self, pid: Optional[int]) -> None:
        if pid is None:
            return
        assert pid in range(1, 4), "PID out of range"
        self._profile_tracker = (pid, self._profile_tracker[1])
        self._state = self.SyncedState.AWAITING_APPLY

    @property
    def rate(self) -> int:
        if self._state == self.SyncedState.UNFETCHED:
            logger.warning("Rate profile not yet fetched from board")
        return self._rate

    @rate.setter
    def rate(self, rate: Optional[int]) -> None:
        if rate is None:
            return
        assert rate in range(1, 7), "Rate out of range"
        self._profile_tracker = (self._profile_tracker[0], rate)
        self._state = self.SyncedState.AWAITING_APPLY

    async def _check_connection(self):
        """Wait for a connection, then get current profiles from board."""
        await self.board.connected.wait()
        await self._set_profiles_from_board()

    @asynccontextmanager
    async def __call__(
        self, pid: Optional[int] = None, rate: Optional[int] = None, revert_on_exit=False
    ) -> AsyncIterator["Profile"]:
        self._state = self.SyncedState.FETCHING

        # wait here till the board is ready
        await self.board.ready.wait()

        logger.debug("Asked to set profiles to: %s", (pid, rate))
        logger.debug("Got current profiles from Board: %s", self._profile_tracker)

        self._revert_to_profiles = (self.pid, self.rate)
        logger.debug("Setting _revert_to_profiles to: %s", self._revert_to_profiles)

        (self.pid, self.rate) = (pid, rate)  # type:ignore

        await self.apply_changes()

        logger.debug("returning profile context")

        yield self
        if revert_on_exit:
            logger.debug("reverting profiles")
            (self.pid, self.rate) = self._revert_to_profiles
            await self.apply_changes()

    async def _set_profiles_from_board(self) -> Tuple[int, int]:
        _, status = await self.board.get(StatusEx)
        if status is None:
            return self._profile_tracker
        self._state = self.SyncedState.CLEAN
        self._profile_tracker = (self._pid, self._rate) = (status.pid_profile, status.rate_profile)
        return self._profile_tracker

    async def _send_pid_to_board(self, pid) -> bool:
        logger.debug("PID profile to: %s", pid)
        p, _ = await self.board.set(SelectPID(pid))
        # return p.message_type != "ERR"
        return True

    async def _send_rate_to_board(self, rate) -> bool:
        logger.debug("Rate profile to: %s", rate)
        p, _ = await self.board.set(SelectRate(rate))
        return True

    async def apply_changes(self) -> bool:
        """Apply any locally changed profiles to the board.

        Returns False if it failed to apply.
        """
        if not self._state == self.SyncedState.AWAITING_APPLY:
            return False
        (asked_pid, asked_rate) = self._profile_tracker
        if asked_pid != self.pid:
            logger.debug("PID profile differs, updating board")
            await self._send_pid_to_board(asked_pid)
        if asked_rate != self.rate:
            logger.debug("Rate profile differs, updating board")
            await self._send_rate_to_board(asked_rate)

        (found_pid, found_rate) = await self._set_profiles_from_board()
        # Sanity check
        if asked_pid != found_pid or asked_rate != found_rate:
            return False
        return True
