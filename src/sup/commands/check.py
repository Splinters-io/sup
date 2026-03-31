"""sup check — scan project dependencies against quarantine thresholds."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from sup.commands.rendering import format_risk
from sup.config import load_config
from sup.lookup import lookup_and_evaluate
from sup.models import Ecosystem, PackageInfo, QuarantineResult, RiskLevel, Tier
from sup.parsers.base import parse_dependencies
from sup.parsers.detect import detect_ecosystem

console = Console()


@click.command()
@click.option(
    "--dir",
    "project_dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=".",
    help="Project directory to scan.",
)
@click.option(
    "--tier",
    type=click.Choice(["known", "bleeding_edge"]),
    default=None,
    help="Quarantine tier (overrides config).",
)
@click.option(
    "--warn-only",
    is_flag=True,
    default=False,
    help="Warn about quarantined packages but exit 0.",
)
@click.option(
    "--type",
    "ecosystem_type",
    type=click.Choice(["python", "node", "go", "rust", "ruby"]),
    default=None,
    help="Force a specific ecosystem (auto-detected by default).",
)
@click.option(
    "--no-cache",
    is_flag=True,
    default=False,
    help="Skip the local cache and query registries directly.",
)
def check(
    project_dir: Path,
    tier: str | None,
    warn_only: bool,
    ecosystem_type: str | None,
    no_cache: bool,
) -> None:
    """Scan project dependencies and enforce quarantine periods."""
    config = load_config()
    warn_only = warn_only or config.warn_only

    active_tier = Tier(tier) if tier else config.default_tier
    required_days = (
        config.known_days if active_tier == Tier.KNOWN else config.bleeding_edge_days
    )
    be_days = config.bleeding_edge_days

    if ecosystem_type:
        ecosystems = [Ecosystem(ecosystem_type)]
    else:
        ecosystems = detect_ecosystem(project_dir)
        if not ecosystems:
            console.print("[red]No supported dependency files found.[/red]")
            sys.exit(1)

    cache_db = None if no_cache else None  # uses default path unless --no-cache

    all_results: list[QuarantineResult] = []

    for eco in ecosystems:
        deps = parse_dependencies(project_dir, eco)
        if not deps:
            continue

        console.print(f"\n[bold]Scanning {eco.value} dependencies...[/bold]")

        for name, version in deps:
            pkg = PackageInfo(name=name, version=version, ecosystem=eco)
            if no_cache:
                from sup.quarantine import evaluate
                from sup.registries import get_client

                client = get_client(eco, base_url=config.registries.get(eco.value))
                publish_date = client.get_publish_date(name, version)
                result = evaluate(pkg, publish_date, required_days, be_days)
            else:
                result = lookup_and_evaluate(
                    pkg, config, required_days, be_days,
                )
            all_results.append(result)

    if not all_results:
        console.print("[yellow]No dependencies found to check.[/yellow]")
        return

    _print_results(all_results, active_tier, required_days)
    _print_summary(all_results, warn_only)


def _print_summary(results: list[QuarantineResult], warn_only: bool) -> None:
    """Print the summary line and exit appropriately."""
    violations = [r for r in results if r.risk_level == RiskLevel.QUARANTINE_VIOLATION]
    bleeding = [r for r in results if r.risk_level == RiskLevel.BLEEDING_EDGE]
    unknowns = [r for r in results if r.risk_level == RiskLevel.UNKNOWN]

    if bleeding:
        console.print(
            f"\n[yellow]{len(bleeding)} package(s) in bleeding edge window "
            f"— past quarantine but recently published. Review recommended.[/yellow]"
        )

    if unknowns:
        console.print(
            f"\n[red]{len(unknowns)} package(s) with unknown publish date "
            f"— cannot verify age.[/red]"
        )

    if violations:
        if warn_only:
            console.print(
                f"\n[yellow]Warning: {len(violations)} quarantine violation(s).[/yellow]"
            )
        else:
            console.print(
                f"\n[red]Blocked: {len(violations)} quarantine violation(s).[/red]"
            )
            sys.exit(1)
    elif unknowns and not warn_only:
        console.print(
            f"\n[red]Blocked: {len(unknowns)} package(s) could not be verified.[/red]"
        )
        sys.exit(1)
    else:
        console.print("\n[green]All packages have passed quarantine.[/green]")


def _print_results(
    results: list[QuarantineResult],
    tier: Tier,
    required_days: int,
) -> None:
    """Print a Rich table of quarantine results."""
    tier_label = tier.value.replace("_", " ").title()
    table = Table(
        title=f"Supply Chain Quarantine Report — tier: {tier_label} ({required_days} days)"
    )
    table.add_column("Package", style="cyan")
    table.add_column("Version", style="magenta")
    table.add_column("Ecosystem", style="blue")
    table.add_column("Age", justify="right")
    table.add_column("Risk")
    table.add_column("Status")

    for r in results:
        age_str = f"{r.age_days}d" if r.age_days is not None else "?"
        risk, status = format_risk(r)
        table.add_row(
            r.package.name, r.package.version, r.package.ecosystem.value,
            age_str, risk, status,
        )

    console.print(table)
