"""Immutable data models for sup."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Tier(Enum):
    """Quarantine tier with default day thresholds."""

    KNOWN = "known"
    BLEEDING_EDGE = "bleeding_edge"


TIER_DEFAULTS: dict[Tier, int] = {
    Tier.KNOWN: 10,
    Tier.BLEEDING_EDGE: 14,
}


class Ecosystem(Enum):
    """Supported package ecosystems."""

    PYTHON = "python"
    NODE = "node"
    GO = "go"
    RUST = "rust"
    RUBY = "ruby"


@dataclass(frozen=True)
class PackageInfo:
    """A dependency with its name, version, and ecosystem."""

    name: str
    version: str
    ecosystem: Ecosystem


class RiskLevel(Enum):
    """Three-state risk classification.

    SAFE:                 Past both Known and BleedingEdge thresholds.
    BLEEDING_EDGE:        Past Known threshold but not BleedingEdge —
                          a flagged risk, not a hard violation.
    QUARANTINE_VIOLATION: Below the active tier's threshold —
                          the package is too new to trust.
    UNKNOWN:              Could not determine publish date.
    """

    SAFE = "safe"
    BLEEDING_EDGE = "bleeding_edge"
    QUARANTINE_VIOLATION = "quarantine_violation"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class QuarantineResult:
    """Result of evaluating a package against quarantine thresholds."""

    package: PackageInfo
    publish_date: datetime | None
    age_days: int | None
    required_days: int
    is_safe: bool
    risk_level: RiskLevel = RiskLevel.SAFE
    error: str | None = None
