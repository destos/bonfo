"""Console script for confo."""

import click


@click.command()
def main():
    """Main entrypoint."""
    click.echo("confo")
    click.echo("=" * len("confo"))
    click.echo("Confo MSP config parsing, validation and packager")


if __name__ == "__main__":
    main()  # pragma: no cover
