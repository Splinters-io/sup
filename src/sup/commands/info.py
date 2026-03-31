"""sup info — show detailed package age information."""

from __future__ import annotations

from datetime import UTC, datetime

import click
from rich.console import Console
from rich.panel import Panel

from sup.models import Ecosystem
from sup.registries import get_client

console = Console()

ECOSYSTEM_CHOICES = ["pypi", "npm", "crates", "go", "rubygems"]
REGISTRY_TO_ECOSYSTEM = {
    "pypi": Ecosystem.PYTHON,
    "npm": Ecosystem.NODE,
    "crates": Ecosystem.RUST,
    "go": Ecosystem.GO,
    "rubygems": Ecosystem.RUBY,
}


@click.command()
@click.argument("package")
@click.option(
    "--registry",
    type=click.Choice(ECOSYSTEM_CHOICES),
    default="pypi",
    help="Which registry to query.",
)
@click.option("--version", "pkg_version", default=None, help="Specific version to check.")
def info(package: str, registry: str, pkg_version: str | None) -> None:
    """Show age details for a package."""
    ecosystem = REGISTRY_TO_ECOSYSTEM[registry]
    client = get_client(ecosystem)

    if pkg_version:
        publish_date = client.get_publish_date(package, pkg_version)
        if publish_date is None:
            console.print(f"[red]Could not find {package}=={pkg_version} on {registry}[/red]")
            return

        now = datetime.now(UTC)
        age = now - publish_date
        console.print(
            Panel(
                f"[bold]{package}[/bold] v{pkg_version}\n"
                f"Registry: {registry}\n"
                f"Published: {publish_date.strftime('%Y-%m-%d %H:%M UTC')}\n"
                f"Age: {age.days} days",
                title="Package Info",
                border_style="cyan",
            )
        )
    else:
        console.print(
            f"[yellow]Use --version to check a specific version of {package}[/yellow]"
        )
