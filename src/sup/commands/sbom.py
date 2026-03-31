"""sup sbom — check, enrich, and report on SBOMs."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from sup import __version__
from sup.commands.rendering import format_risk
from sup.config import SupConfig, load_config
from sup.models import PackageInfo, QuarantineResult, RiskLevel, Tier
from sup.quarantine import evaluate, quarantine_ends
from sup.registries import get_client
from sup.sbom.enrich import enrich_sbom, write_enriched_sbom
from sup.sbom.parse import parse_sbom

console = Console()


@click.group()
def sbom() -> None:
    """Work with Software Bills of Materials (SBOMs)."""


@sbom.command()
@click.argument("sbom_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--tier",
    type=click.Choice(["known", "bleeding_edge"]),
    default=None,
    help="Quarantine tier (overrides config).",
)
@click.option("--warn-only", is_flag=True, default=False, help="Warn but exit 0.")
def check(sbom_path: Path, tier: str | None, warn_only: bool) -> None:
    """Check an SBOM's components against quarantine thresholds."""
    config = load_config()
    warn_only = warn_only or config.warn_only
    active_tier, required_days, be_days = _resolve_tier(config, tier)

    try:
        fmt, packages, _raw = parse_sbom(sbom_path)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)

    console.print(f"[bold]Parsed {fmt.value} SBOM:[/bold] {len(packages)} components")

    results = _evaluate_packages(packages, config, required_days, be_days)
    _print_results(results, active_tier, required_days)
    _exit_with_status(results, warn_only)


@sbom.command()
@click.argument("sbom_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--output", "-o",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Output path for enriched SBOM (default: <input>.enriched.json).",
)
@click.option(
    "--tier",
    type=click.Choice(["known", "bleeding_edge"]),
    default=None,
    help="Quarantine tier (overrides config).",
)
def enrich(sbom_path: Path, output: Path | None, tier: str | None) -> None:
    """Enrich an SBOM with quarantine annotations and export."""
    config = load_config()
    active_tier, required_days, be_days = _resolve_tier(config, tier)

    try:
        fmt, packages, raw_data = parse_sbom(sbom_path)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)

    console.print(f"[bold]Parsed {fmt.value} SBOM:[/bold] {len(packages)} components")

    results = _evaluate_packages(packages, config, required_days, be_days)
    enriched = enrich_sbom(raw_data, fmt, results, active_tier.value, required_days)

    output_path = output or sbom_path.with_suffix(".enriched.json")
    write_enriched_sbom(enriched, output_path)

    _print_enrich_summary(results, output_path)


@sbom.command()
@click.argument("sbom_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--tier",
    type=click.Choice(["known", "bleeding_edge"]),
    default=None,
    help="Quarantine tier (overrides config).",
)
@click.option(
    "--output", "-o",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Write report to file (default: print to terminal).",
)
def report(sbom_path: Path, tier: str | None, output: Path | None) -> None:
    """Generate a human-readable quarantine report for an SBOM."""
    config = load_config()
    active_tier, required_days, be_days = _resolve_tier(config, tier)

    try:
        fmt, packages, _raw = parse_sbom(sbom_path)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)

    results = _evaluate_packages(packages, config, required_days, be_days)
    report_text = _build_report(
        sbom_path, fmt.value, results, active_tier, required_days, be_days,
    )

    if output:
        output.write_text(report_text)
        console.print(f"[bold]Report written to:[/bold] {output}")
    else:
        console.print(report_text)


# --- shared helpers ---


def _resolve_tier(
    config: SupConfig, tier_str: str | None,
) -> tuple[Tier, int, int]:
    """Return (active_tier, required_days, bleeding_edge_days)."""
    active_tier = Tier(tier_str) if tier_str else config.default_tier
    required_days = (
        config.known_days if active_tier == Tier.KNOWN else config.bleeding_edge_days
    )
    return active_tier, required_days, config.bleeding_edge_days


def _evaluate_packages(
    packages: list[PackageInfo],
    config: SupConfig,
    required_days: int,
    be_days: int,
) -> list[QuarantineResult]:
    """Query registries and evaluate quarantine status for each package."""
    results: list[QuarantineResult] = []
    for pkg in packages:
        client = get_client(pkg.ecosystem, base_url=config.registries.get(pkg.ecosystem.value))
        publish_date = client.get_publish_date(pkg.name, pkg.version)
        result = evaluate(pkg, publish_date, required_days, be_days)
        results.append(result)
    return results


def _exit_with_status(results: list[QuarantineResult], warn_only: bool) -> None:
    """Print summary and exit."""
    violations = [r for r in results if r.risk_level == RiskLevel.QUARANTINE_VIOLATION]
    bleeding = [r for r in results if r.risk_level == RiskLevel.BLEEDING_EDGE]
    unknowns = [r for r in results if r.risk_level == RiskLevel.UNKNOWN]

    if bleeding:
        console.print(
            f"\n[yellow]{len(bleeding)} component(s) in bleeding edge window "
            f"— past quarantine but recently published. Review recommended.[/yellow]"
        )

    if unknowns:
        console.print(
            f"\n[red]{len(unknowns)} component(s) with unknown publish date.[/red]"
        )

    if violations:
        if warn_only:
            console.print(f"\n[yellow]Warning: {len(violations)} quarantine violation(s).[/yellow]")
        else:
            console.print(f"\n[red]Blocked: {len(violations)} quarantine violation(s).[/red]")
            sys.exit(1)
    elif unknowns and not warn_only:
        console.print(f"\n[red]Blocked: could not verify {len(unknowns)} component(s).[/red]")
        sys.exit(1)
    else:
        console.print("\n[green]All SBOM components have passed quarantine.[/green]")


def _print_results(
    results: list[QuarantineResult],
    tier: Tier,
    required_days: int,
) -> None:
    """Print a Rich table of quarantine results."""
    tier_label = tier.value.replace("_", " ").title()
    table = Table(
        title=f"SBOM Quarantine Report — tier: {tier_label} ({required_days} days)"
    )
    table.add_column("Component", style="cyan")
    table.add_column("Version", style="magenta")
    table.add_column("Ecosystem", style="blue")
    table.add_column("Age", justify="right")
    table.add_column("Risk")
    table.add_column("Status")

    for r in results:
        age_str = f"{r.age_days}d" if r.age_days is not None else "?"
        risk, status = _format_risk(r)
        table.add_row(
            r.package.name, r.package.version, r.package.ecosystem.value,
            age_str, risk, status,
        )

    console.print(table)


_format_risk = format_risk


def _print_enrich_summary(results: list[QuarantineResult], output_path: Path) -> None:
    """Summary after enrichment."""
    safe = sum(1 for r in results if r.risk_level == RiskLevel.SAFE)
    bleeding = sum(1 for r in results if r.risk_level == RiskLevel.BLEEDING_EDGE)
    violations = sum(1 for r in results if r.risk_level == RiskLevel.QUARANTINE_VIOLATION)
    unknown = sum(1 for r in results if r.risk_level == RiskLevel.UNKNOWN)

    console.print(f"\n[bold]Enriched SBOM written to:[/bold] {output_path}")
    console.print(f"  Components:           {len(results)}")
    console.print(f"  Safe:                 [green]{safe}[/green]")
    if bleeding:
        console.print(f"  Bleeding edge:        [yellow]{bleeding}[/yellow]")
    if violations:
        console.print(f"  Quarantine violations: [red]{violations}[/red]")
    if unknown:
        console.print(f"  Unknown:              [red]{unknown}[/red]")


def _build_report(
    sbom_path: Path,
    fmt_name: str,
    results: list[QuarantineResult],
    tier: Tier,
    required_days: int,
    be_days: int,
) -> str:
    """Build a plain-text quarantine report."""
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    tier_label = tier.value.replace("_", " ").title()

    safe = [r for r in results if r.risk_level == RiskLevel.SAFE]
    bleeding = [r for r in results if r.risk_level == RiskLevel.BLEEDING_EDGE]
    violations = [r for r in results if r.risk_level == RiskLevel.QUARANTINE_VIOLATION]
    unknown = [r for r in results if r.risk_level == RiskLevel.UNKNOWN]

    lines: list[str] = []
    lines.append("# Supply Chain Quarantine Report")
    lines.append("")
    lines.append(f"Generated: {now}")
    lines.append(f"SBOM:      {sbom_path.name} ({fmt_name})")
    lines.append(f"Tier:      {tier_label} ({required_days}-day threshold)")
    lines.append(f"Bleeding edge window: {required_days}–{be_days} days")
    lines.append(f"Components scanned: {len(results)}")
    lines.append("")

    # Verdict
    if violations:
        lines.append(f"VERDICT: FAIL — {len(violations)} quarantine violation(s)")
    elif unknown:
        lines.append(f"VERDICT: FAIL — {len(unknown)} component(s) could not be verified")
    elif bleeding:
        lines.append(f"VERDICT: PASS with {len(bleeding)} bleeding edge flag(s)")
    else:
        lines.append("VERDICT: PASS — all components cleared quarantine")
    lines.append("")

    # Breakdown
    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Classification         | Count |")
    lines.append(f"|------------------------|-------|")
    lines.append(f"| Safe (>{be_days}d)     | {len(safe):>5} |")
    lines.append(f"| Bleeding edge ({required_days}–{be_days}d) | {len(bleeding):>5} |")
    lines.append(f"| Quarantine violation (<{required_days}d) | {len(violations):>5} |")
    lines.append(f"| Unknown                | {len(unknown):>5} |")
    lines.append("")

    # Quarantine violations — these are the blockers
    if violations:
        lines.append("## Quarantine Violations")
        lines.append("")
        lines.append("These components are too new to trust. They must age past the")
        lines.append(f"{required_days}-day threshold before they can be used.")
        lines.append("")
        lines.append("| Component | Version | Ecosystem | Age | Clears on |")
        lines.append("|-----------|---------|-----------|-----|-----------|")
        for r in violations:
            ends = quarantine_ends(r.publish_date, r.required_days)  # type: ignore[arg-type]
            lines.append(
                f"| {r.package.name} | {r.package.version} | "
                f"{r.package.ecosystem.value} | {r.age_days}d | "
                f"{ends.strftime('%Y-%m-%d')} |"
            )
        lines.append("")

    # Bleeding edge — flagged risks, not blockers
    if bleeding:
        lines.append("## Bleeding Edge Components")
        lines.append("")
        lines.append(f"These components are past the {required_days}-day quarantine threshold")
        lines.append(f"but within the {be_days}-day bleeding edge window. They are not")
        lines.append("blocked, but carry elevated supply chain risk. Manual review is")
        lines.append("recommended before use in production.")
        lines.append("")
        lines.append("| Component | Version | Ecosystem | Age | Fully clears on |")
        lines.append("|-----------|---------|-----------|-----|-----------------|")
        for r in bleeding:
            full_clear = quarantine_ends(r.publish_date, be_days)  # type: ignore[arg-type]
            lines.append(
                f"| {r.package.name} | {r.package.version} | "
                f"{r.package.ecosystem.value} | {r.age_days}d | "
                f"{full_clear.strftime('%Y-%m-%d')} |"
            )
        lines.append("")

    # Unknown
    if unknown:
        lines.append("## Unverifiable Components")
        lines.append("")
        lines.append("Publish dates could not be determined for these components.")
        lines.append("This may be due to private registries, yanked versions, or")
        lines.append("registry API limitations (e.g. npm dropped the time field in 2021).")
        lines.append("")
        for r in unknown:
            lines.append(f"- {r.package.name} {r.package.version} ({r.package.ecosystem.value}): {r.error}")
        lines.append("")

    # Safe — just a count, no need to list them all
    if safe:
        lines.append("## Safe Components")
        lines.append("")
        lines.append(f"{len(safe)} component(s) have been published for more than")
        lines.append(f"{be_days} days and carry low supply chain risk.")
        lines.append("")

    lines.append("---")
    lines.append(f"Generated by sup-quarantine v{__version__}")

    return "\n".join(lines)
