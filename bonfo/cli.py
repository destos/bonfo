"""Console script for bonfo."""

import atexit
import logging
import os
import shelve
import sys
from dataclasses import dataclass
from time import sleep
from typing import Optional, Sequence

import rich_click as click
from construct import ChecksumError, ConstError
from loca import Loca
from rich import print
from serial.tools.list_ports import comports
from serial.tools.list_ports_common import ListPortInfo

from bonfo.msp.board import Board
from bonfo.msp.codes import MSP

click.rich_click.USE_MARKDOWN = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True

logger = logging.getLogger(__name__)

logging.basicConfig(
    format="[%(levelname)s] [%(asctime)s]: %(message)s", level=getattr(logging, "DEBUG"), stream=sys.stdout
)

# config things
try:
    loca = Loca()
    path = loca.user.state.config()
    if isinstance(path, list):
        path = path.pop()
    bonfo_state_dir = path / "bonfo"
    state_file = str(bonfo_state_dir / "cli_state")
    os.makedirs(bonfo_state_dir)
except FileExistsError:
    pass
finally:
    logger.debug("State file: %s", state_file)
    state_store = shelve.open(state_file, flag="c")


@dataclass
class BonfoContext:
    # TODO: hook/bring in state_store as a storage backend, possible change to data class and use the data class wizard?
    port: Optional[ListPortInfo] = None
    # Go this direction of only working on one rate/pid profile?
    # Profile to switch to
    # profile: = None
    # Rate profile to act on
    # rate_profile: = None

    _board = None

    @property
    def board(self) -> Optional[Board]:
        if self._board is None and self.port is not None:
            # TODO: instantiate board with stored values to do diffing?
            # Possibly on board connect, it grabs the uid of the board and hydrates from
            # last state that way?
            self._board = Board(self.port.device)
        return self._board


bonfo_context = click.make_pass_decorator(BonfoContext)


@click.group("bonfo")
@click.pass_context
def cli(ctx):
    """Bonfo is configuration management for flight controllers running **MSP v1** compatible flight controllers.

    > Supported flight controller software:
    >  - BetaFlight
    """
    ctx.obj = BonfoContext(port=state_store.get("port", None))


@cli.command()
@bonfo_context
def check_context(ctx):
    """Output current context values."""
    print(ctx.board)
    print(ctx.port)


@cli.command()
@bonfo_context
def connect(ctx: BonfoContext):
    """Connect to the FC board."""
    if ctx.board is None:
        return click.echo("No port selected")
    with ctx.board as board:
        click.echo(board.send_msg(MSP.API_VERSION))


@cli.command()
@bonfo_context
def update(ctx: BonfoContext):
    if ctx.board is None:
        return click.echo("No port selected")
    with ctx.board as board:
        while True:
            sleep(1)
            click.echo(board.send_msg(MSP.STATUS_EX))
            try:
                click.echo(board.receive_msg())
            except (ChecksumError, ConstError) as e:
                logger.exception("error", exc_info=e)


@cli.command()
@bonfo_context
@click.option('-s', '--include-links', is_flag=True, help='include entries that are symlinks to real devices')
def set_port(cxt, include_links, err=True):
    """Set the default port to use during this session."""
    # TODO: let user know they are changing the port from the context if it changes
    # or show current as well
    iterator = sorted(comports(include_links=include_links))
    ports = {n: lpi for n, lpi in enumerate(iterator, 1)}
    for n, (port, desc, hwid) in ports.items():
        click.echo(f"{n}: {port}, {desc}, {hwid}")
    port = click.prompt("Select a port", show_choices=True, value_proc=int)
    try:
        selected = ports[port]
        click.echo(f"Selected: {selected}")
        state_store["port"] = selected
    except IndexError:
        click.Abort()


@cli.command()
@click.pass_context
def make_snapshot():
    pass


def main():
    cli(prog_name="bonfo")


if __name__ == "__main__":
    atexit.register(state_store.close)
    main()  # pragma: no cover

__all__: Sequence[str] = []
