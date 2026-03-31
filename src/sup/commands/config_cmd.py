"""sup config — manage sup configuration."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from sup.config import CONFIG_PATH, init_config, load_config

console = Console()


@click.command("config")
@click.option("--init", "do_init", is_flag=True, help="Create default config file.")
@click.option("--show", "do_show", is_flag=True, help="Show current configuration.")
def config_cmd(do_init: bool, do_show: bool) -> None:
    """Manage sup configuration."""
    if do_init:
        path = init_config()
        console.print(f"[green]Config created at: {path}[/green]")
        return

    if do_show:
        cfg = load_config()
        console.print(f"[bold]Config file:[/bold] {CONFIG_PATH}")
        console.print(f"  Known tier:         {cfg.known_days} days")
        console.print(f"  Bleeding edge tier: {cfg.bleeding_edge_days} days")
        console.print(f"  Default tier:       {cfg.default_tier.value}")
        console.print(f"  Warn only:          {cfg.warn_only}")
        if cfg.registries:
            console.print("  Custom registries:")
            for name, url in cfg.registries.items():
                console.print(f"    {name}: {url}")
        return

    # Default: show help
    ctx = click.get_current_context()
    click.echo(ctx.get_help())
