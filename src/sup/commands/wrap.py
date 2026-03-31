"""sup wrap — intercept install commands and quarantine-check before proceeding.

Usage:
    sup wrap pip install requests==2.31.0
    sup wrap npm install express@4.18.2
    sup wrap -- pip install -r requirements.txt
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console

from sup.config import load_config
from sup.lookup import lookup_and_evaluate
from sup.models import Ecosystem, PackageInfo, RiskLevel, Tier

console = Console()

# Patterns for extracting package specs from install commands
_PIP_SPEC = re.compile(r"^([a-zA-Z0-9._-]+)==([^\s]+)$")
_PIP_NAME = re.compile(r"^([a-zA-Z0-9._-]+)$")
_NPM_SPEC = re.compile(r"^(@?[a-zA-Z0-9._/-]+)@([^\s]+)$")
_NPM_NAME = re.compile(r"^(@?[a-zA-Z0-9._/-]+)$")

# Map package manager to ecosystem
_PM_ECOSYSTEM: dict[str, Ecosystem] = {
    "pip": Ecosystem.PYTHON,
    "pip3": Ecosystem.PYTHON,
    "npm": Ecosystem.NODE,
    "yarn": Ecosystem.NODE,
    "go": Ecosystem.GO,
    "cargo": Ecosystem.RUST,
    "gem": Ecosystem.RUBY,
    "bundle": Ecosystem.RUBY,
}


@click.command(
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.argument("command", nargs=-1, required=True)
@click.option("--warn-only", is_flag=True, default=False, help="Warn but don't block.")
@click.option(
    "--tier",
    type=click.Choice(["known", "bleeding_edge"]),
    default=None,
    help="Quarantine tier.",
)
@click.pass_context
def wrap(ctx: click.Context, command: tuple[str, ...], warn_only: bool, tier: str | None) -> None:
    """Wrap a package install command with quarantine checks.

    Parses the install command for package names/versions, checks them
    against quarantine thresholds, then either proceeds or blocks.

    \b
    Examples:
        sup wrap pip install requests==2.31.0
        sup wrap npm install express@4.18.2
        sup wrap -- cargo add serde@1.0.197
    """
    config = load_config()
    warn_only = warn_only or config.warn_only

    active_tier = Tier(tier) if tier else config.default_tier
    required_days = (
        config.known_days if active_tier == Tier.KNOWN else config.bleeding_edge_days
    )
    be_days = config.bleeding_edge_days

    pm = command[0]
    ecosystem = _PM_ECOSYSTEM.get(pm)

    if ecosystem is None:
        console.print(f"[yellow]Unknown package manager: {pm}. Running without checks.[/yellow]")
        sys.exit(subprocess.call(list(command)))

    # Extract package specs from command args
    packages = _extract_packages(command, ecosystem)

    if not packages:
        # No parseable package specs — just pass through (e.g., pip install -r requirements.txt)
        console.print("[dim]No inline package specs detected. Running command...[/dim]")
        exit_code = subprocess.call(list(command))
        if exit_code == 0:
            console.print(
                "[dim]Tip: run [bold]sup check[/bold] after install to verify lockfile.[/dim]"
            )
        sys.exit(exit_code)

    # Check each package
    blocked: list[tuple[PackageInfo, str]] = []
    for pkg in packages:
        result = lookup_and_evaluate(pkg, config, required_days, be_days)
        if result.risk_level == RiskLevel.QUARANTINE_VIOLATION:
            blocked.append((pkg, f"age {result.age_days}d < {required_days}d threshold"))
        elif result.risk_level == RiskLevel.UNKNOWN:
            blocked.append((pkg, result.error or "unknown publish date"))
        elif result.risk_level == RiskLevel.BLEEDING_EDGE:
            console.print(
                f"[yellow]  {pkg.name}=={pkg.version}: bleeding edge "
                f"({result.age_days}d) — review recommended[/yellow]"
            )

    if blocked:
        console.print(f"\n[red]Quarantine check failed for {len(blocked)} package(s):[/red]")
        for pkg, reason in blocked:
            console.print(f"  [red]{pkg.name}=={pkg.version}: {reason}[/red]")

        if warn_only:
            console.print("\n[yellow]--warn-only: proceeding anyway.[/yellow]")
        else:
            console.print("\n[red]Install blocked. Use --warn-only to override,[/red]")
            console.print("[red]or: sup allow add PACKAGE VERSION -r 'reason' --by you[/red]")
            sys.exit(1)

    # All clear — run the actual command
    console.print(f"[green]Quarantine check passed. Running: {' '.join(command)}[/green]")
    sys.exit(subprocess.call(list(command)))


def _extract_packages(
    command: tuple[str, ...],
    ecosystem: Ecosystem,
) -> list[PackageInfo]:
    """Extract package name+version pairs from an install command."""
    args = list(command)
    pm = args[0]
    packages: list[PackageInfo] = []

    # Skip the package manager name and the subcommand (install/add)
    skip_next = False
    for arg in args[1:]:
        if skip_next:
            skip_next = False
            continue
        # Skip flags and their arguments
        if arg.startswith("-"):
            if arg in ("-r", "--requirement", "-e", "--editable", "-t", "--target"):
                skip_next = True
            continue
        # Skip subcommands
        if arg in ("install", "add", "i", "get"):
            continue

        pkg = _parse_package_spec(arg, ecosystem)
        if pkg:
            packages.append(pkg)

    return packages


def _parse_package_spec(spec: str, ecosystem: Ecosystem) -> PackageInfo | None:
    """Parse a single package spec like 'requests==2.31.0' or 'express@4.18.2'."""
    if ecosystem in (Ecosystem.PYTHON,):
        match = _PIP_SPEC.match(spec)
        if match:
            return PackageInfo(name=match.group(1), version=match.group(2), ecosystem=ecosystem)
        # pip install requests (no version) — can't check, skip
        return None

    if ecosystem in (Ecosystem.NODE,):
        match = _NPM_SPEC.match(spec)
        if match:
            return PackageInfo(name=match.group(1), version=match.group(2), ecosystem=ecosystem)
        return None

    if ecosystem == Ecosystem.RUST:
        # cargo add serde@1.0.197
        if "@" in spec:
            parts = spec.rsplit("@", 1)
            if len(parts) == 2 and parts[1]:
                return PackageInfo(name=parts[0], version=parts[1], ecosystem=ecosystem)
        return None

    if ecosystem == Ecosystem.GO:
        # go get github.com/gin-gonic/gin@v1.9.1
        if "@" in spec:
            parts = spec.rsplit("@", 1)
            if len(parts) == 2 and parts[1]:
                return PackageInfo(name=parts[0], version=parts[1], ecosystem=ecosystem)
        return None

    # Ruby: gem install rails -v 7.1.2 — version is a flag, hard to parse inline
    return None
