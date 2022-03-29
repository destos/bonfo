"""Console script for confo."""

from dataclasses import dataclass
import logging
import sys
import shelve
import os
from time import sleep
from typing import NamedTuple, Optional
from construct import ChecksumError, ConstError

import rich_click as click
from loca import Loca
from serial.tools.list_ports import comports
from serial.tools.list_ports_common import ListPortInfo
import atexit

from rich import print
from confo.msp import FlightController

from confo.msp.board import Board
from confo.msp.codes import MSP

click.rich_click.USE_MARKDOWN = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True

logger = logging.getLogger(__name__)

logging.basicConfig(
    format="[%(levelname)s] [%(asctime)s]: %(message)s", level=getattr(logging, "DEBUG"), stream=sys.stdout
)

# config stuff
try:
    loca = Loca()
    confo_state_dir = loca.user.state.config() / "confo"
    state_file = str(confo_state_dir / "cli_state")
    os.makedirs(confo_state_dir)
except FileExistsError:
    pass
finally:
    logger.debug("State file: %s", state_file)
    state_store = shelve.open(state_file, flag="c")


@dataclass
class ConfoContext:
    port: Optional[ListPortInfo] = None

    _board = None

    @property
    def board(self) -> Optional[Board]:
        if self._board is None and self.port is not None:
            self._board = Board(self.port.device)
        return self._board


confo_context = click.make_pass_decorator(ConfoContext)


@click.group("confo")
@click.pass_context
def cli(ctx):
    """
    Configuration management for flight controllers running **MSP v1** compatible flight controllers.

    > Supported flight controller software:
    >  - BetaFlight
    """
    # board=state_store.get("board", None),
    ctx.obj = ConfoContext(port=state_store.get("port", None))


@cli.command()
@confo_context
def check_context(ctx):
    print(ctx.board)
    print(ctx.port)


@cli.command()
@confo_context
def connect(ctx: ConfoContext):
    "Connect to the FC board"
    with ctx.board as board:
        click.echo(board.send_msg(MSP.API_VERSION))


@cli.command()
@confo_context
def update(ctx: ConfoContext):

    # with FlightController(ctx.port.device) as fc:
    with ctx.board as board:
        while True:
            sleep(1)
            click.echo(board.send_msg(MSP.STATUS_EX))
            # click.echo(board.send_msg(MSP.RAW_IMU))
            try:
                click.echo(board.receive_msg())
            except (ChecksumError, ConstError) as e:
                logger.exception("error", exc_info=e)


@cli.command()
@confo_context
@click.option('-s', '--include-links', is_flag=True, help='include entries that are symlinks to real devices')
def set_port(cxt, include_links, err=True):
    # TODO: let user know they are changing the port from the context if it changes
    # or show current as well
    """Set the default port to use during this session."""
    iterator = sorted(comports(include_links=include_links))
    ports = {n: lpi for n, lpi in enumerate(iterator, 1)}
    for n, (port, desc, hwid) in ports.items():
        # for n, p in ports:
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


# comports
def main():
    cli(prog_name="confo")


if __name__ == "__main__":
    atexit.register(state_store.close)
    main()  # pragma: no cover
