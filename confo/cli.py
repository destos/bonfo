"""Console script for confo."""

import logging
import sys

import click

from confo.msp import FlightController

logger = logging.getLogger(__name__)

logging.basicConfig(
    format="[%(levelname)s] [%(asctime)s]: %(message)s", level=getattr(logging, "INFO"), stream=sys.stdout
)


@click.command()
def main():
    """Main entrypoint."""
    dev = "/dev/tty.usbmodem0x80000001"
    click.echo(dev)
    with FlightController(dev) as fc:
        click.echo(fc.conf)
        click.echo(fc.rx_conf)
        click.echo(fc.rc_tuning)
        file_name = f"{'_'.join(str(u) for u in fc.conf.uid)}_rc_runing.yaml"
        fc.rc_tuning.to_yaml_file(file_name)

    # click.echo()
    # click.echo("Confo MSP config parsing, validation and packager")


if __name__ == "__main__":
    main()  # pragma: no cover
