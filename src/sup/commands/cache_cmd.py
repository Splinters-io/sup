"""sup cache — manage the local registry cache."""

from __future__ import annotations

import click
from rich.console import Console

from sup.cache import cache_stats, clear_cache

console = Console()


@click.group("cache")
def cache_cmd() -> None:
    """Manage the local registry cache."""


@cache_cmd.command("clear")
def cache_clear() -> None:
    """Clear all cached registry data."""
    count = clear_cache()
    console.print(f"[green]Cleared {count} cached entries.[/green]")


@cache_cmd.command("stats")
def cache_show_stats() -> None:
    """Show cache statistics."""
    stats = cache_stats()
    console.print(f"  Total entries: {stats['total']}")
    console.print(f"  Fresh (<24h):  [green]{stats['fresh']}[/green]")
    console.print(f"  Expired:       [dim]{stats['expired']}[/dim]")
