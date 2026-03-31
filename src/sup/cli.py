"""Main CLI entry point for sup."""

import click

from sup import __version__
from sup.commands.allow import allow
from sup.commands.cache_cmd import cache_cmd
from sup.commands.check import check
from sup.commands.config_cmd import config_cmd
from sup.commands.info import info
from sup.commands.init import init
from sup.commands.sbom import sbom
from sup.commands.wrap import wrap


@click.group()
@click.version_option(version=__version__, prog_name="sup")
def cli() -> None:
    """sup — Supply chain quarantine tool.

    Enforce age gates on dependency updates to mitigate supply chain attacks.
    """


cli.add_command(allow)
cli.add_command(cache_cmd)
cli.add_command(check)
cli.add_command(config_cmd)
cli.add_command(info)
cli.add_command(init)
cli.add_command(sbom)
cli.add_command(wrap)
