"""Console script for bonfo."""

import asyncio
import atexit
import functools
import logging
import os
import shelve
import sys
from dataclasses import dataclass
from typing import Optional, Sequence

import rich_click as click
from loca import Loca
from rich import print
from serial.tools.list_ports import comports
from serial.tools.list_ports_common import ListPortInfo

from bonfo.board import Board
from bonfo.msp.codes import MSP
from bonfo.msp.fields.boxes import BoxIds

click.rich_click.USE_MARKDOWN = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True

logger = logging.getLogger(__name__)

logging.basicConfig(
    format="[%(levelname)s] [%(asctime)s]: %(message)s", level=getattr(logging, "DEBUG"), stream=sys.stdout
)

# config things
# TODO: use datawizard instead, and init the board/port via property.
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
    try:
        state_store = shelve.open(state_file, flag="c")
    except Exception as e:
        logger.exception("Error loading state", exc_info=e)


def async_cmd(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper


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
    """Bonfo is configuration management for flight controllers running **MSP v1**.

    > Supported flight controller software:
    >  - BetaFlight(>=3.4)
    """
    ctx.obj = BonfoContext(port=state_store.get("port", None))


@cli.command()
@bonfo_context
def check_context(ctx: BonfoContext):
    """Output current context values."""
    print(ctx.board)
    print(ctx.port)


@cli.command()
@bonfo_context
def connect(ctx: BonfoContext):
    """Connect to the FC board."""
    if ctx.board is None:
        return click.echo("No port selected")
    with ctx.board.connect() as board:
        click.echo(board.send_msg(MSP.API_VERSION))


@cli.command()
@bonfo_context
@async_cmd
async def test(ctx: BonfoContext):
    """Just me, testing things."""
    if ctx.board is None:
        return click.echo("No port selected")
    async with ctx.board.connect() as board:
        pass
        # print(board.info)
        # print(str(board.profile))
        # status = await board.get(StatusEx)
        # print(status)
        # print(Name(name="bobby").build())
        # name = await (board < Name(name="robby"))
        # print(name)
        # name = await (board > Name)
        # sensor = await (board > SensorAlignment)
        # att = await (board > BoxIds)
        # pid = await (board > BoxNames)
        fc = await (board > BoxIds)
        print(fc)
        # fc.features &= Features.ESC_SENSOR
        # breakpoint()
        # await (board < fc)
        # fcsecond = await (board > FeatureConfig)
        # print(name)
        # print(att)
        # print(sensor)
        # print(fcres)
        # print(fcsecond)
        # while True:
        #     att = await (board > Attitude)
        #     print(att)
        # await asyncio.sleep(0.01)
        # print(pid)


@cli.command()
@bonfo_context
@async_cmd
async def msp_cli(ctx: BonfoContext):
    """Drop into the MSP CLI"""
    if ctx.board is None:
        return click.echo("No port selected")
    async with ctx.board.connect() as board:
        board.writer.write(b"#")
        while True:
            line = await board.reader.readline()
            print(line)
            cmd = click.prompt("$")
            board.writer.write(cmd)


@cli.group("profiles")
@bonfo_context
def profiles(ctx: BonfoContext):
    pass


@profiles.command()
@bonfo_context
@async_cmd
async def get(ctx: BonfoContext):
    """Get the PID and rate profile of the flight controller."""
    if ctx.board is None:
        return click.echo("No port selected")
    async with ctx.board.connect() as board:
        click.echo(f"{board.profile}")


@profiles.command()
@bonfo_context
@click.option("-p", "--pid", type=int)
@click.option("-r", "--rate", type=int)
@async_cmd
async def set(ctx: BonfoContext, pid, rate):
    """Set the PID or rate profile of the flight controller."""
    if ctx.board is None:
        return click.echo("No port selected")
    async with ctx.board.connect() as board:
        click.echo(f"Before: {board.profile}")
        if pid is not None:
            board.profile.pid = pid
        if rate is not None:
            board.profile.rate = rate
        await board.profile.apply_changes()
        click.echo(f"After: {board.profile}")


@cli.group("config")
@bonfo_context
def config(ctx: BonfoContext):
    """Manage and apply configuration files."""
    pass


@config.command()
@bonfo_context
@click.option("-c", "--check", type=bool)
@click.argument("file", type=click.File("r"))
def apply(ctx: BonfoContext, check, file):
    """Apply passed configuration."""
    pass
    # click.echo(BoardConf.from_yaml(file.read()))


@config.command()
@bonfo_context
@click.argument("file", type=click.Path(dir_okay=False))
def create(ctx: BonfoContext, file):
    pass
    # BoardConf(
    #     pid_profiles={1: PidTranslator(test_one=123, test2=123), 2: PidTranslator(test_one=3, test2=4)},
    #     # rates=[RateTranslator(profile=1, yaw=123)]
    # ).to_yaml_file(file)


@cli.command()
@bonfo_context
@click.option("-s", "--include-links", is_flag=True, help="include entries that are symlinks to real devices")
def set_port(cxt: BonfoContext, include_links, err=True):
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
