"""sup allow — manage the package allowlist."""

from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from sup.allowlist import (
    add_to_allowlist,
    load_allowlist,
    remove_from_allowlist,
)

console = Console()


@click.group()
def allow() -> None:
    """Manage the quarantine allowlist."""


@allow.command("add")
@click.argument("package")
@click.argument("version", default="*")
@click.option("--reason", "-r", required=True, help="Why this package was reviewed and approved.")
@click.option("--by", "reviewed_by", required=True, help="Who reviewed this package.")
def allow_add(package: str, version: str, reason: str, reviewed_by: str) -> None:
    """Add a package to the allowlist (bypasses quarantine).

    VERSION defaults to * (all versions).
    """
    entry = add_to_allowlist(package, version, reason, reviewed_by)
    console.print(
        f"[green]Allowed:[/green] {entry.package}@{entry.version} "
        f"(by {entry.reviewed_by}, {entry.reviewed_at})"
    )


@allow.command("remove")
@click.argument("package")
@click.argument("version", default="*")
def allow_remove(package: str, version: str) -> None:
    """Remove a package from the allowlist."""
    if remove_from_allowlist(package, version):
        console.print(f"[green]Removed:[/green] {package}@{version}")
    else:
        console.print(f"[yellow]Not found:[/yellow] {package}@{version}")


@allow.command("list")
def allow_list() -> None:
    """Show all allowlisted packages."""
    entries = load_allowlist()
    if not entries:
        console.print("[dim]Allowlist is empty.[/dim]")
        return

    table = Table(title="Quarantine Allowlist")
    table.add_column("Package", style="cyan")
    table.add_column("Version", style="magenta")
    table.add_column("Reason")
    table.add_column("Reviewed by")
    table.add_column("Date")

    for e in entries:
        table.add_row(e.package, e.version, e.reason, e.reviewed_by, e.reviewed_at)

    console.print(table)
