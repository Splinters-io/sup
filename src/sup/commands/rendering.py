"""Shared rendering helpers for CLI commands."""

from __future__ import annotations

from sup.models import QuarantineResult, RiskLevel
from sup.quarantine import quarantine_ends


def format_risk(r: QuarantineResult) -> tuple[str, str]:
    """Return (risk_label, status_label) for a quarantine result."""
    match r.risk_level:
        case RiskLevel.SAFE:
            return "[green]low[/green]", "[green]safe[/green]"
        case RiskLevel.BLEEDING_EDGE:
            return (
                "[yellow]elevated[/yellow]",
                "[yellow]bleeding edge — review recommended[/yellow]",
            )
        case RiskLevel.QUARANTINE_VIOLATION:
            assert r.publish_date is not None
            ends = quarantine_ends(r.publish_date, r.required_days)
            return (
                "[red]high[/red]",
                f"[red]QUARANTINE VIOLATION (until {ends.strftime('%Y-%m-%d')})[/red]",
            )
        case RiskLevel.UNKNOWN:
            error = r.error or "unknown"
            return "[red]unknown[/red]", f"[red]{error}[/red]"
