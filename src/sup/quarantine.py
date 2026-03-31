"""Core quarantine evaluation logic."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sup.models import PackageInfo, QuarantineResult, RiskLevel


def evaluate(
    package: PackageInfo,
    publish_date: datetime | None,
    required_days: int,
    bleeding_edge_days: int | None = None,
) -> QuarantineResult:
    """Evaluate a package version against quarantine thresholds.

    Args:
        package: The package to evaluate.
        publish_date: When the version was published (None if unknown).
        required_days: The active tier's threshold in days.
        bleeding_edge_days: The bleeding edge threshold. When provided,
            packages between required_days and bleeding_edge_days are
            classified as BLEEDING_EDGE risk (flagged, not blocked).

    Returns an immutable QuarantineResult.
    """
    if publish_date is None:
        return QuarantineResult(
            package=package,
            publish_date=None,
            age_days=None,
            required_days=required_days,
            is_safe=False,
            risk_level=RiskLevel.UNKNOWN,
            error="Could not determine publish date",
        )

    now = datetime.now(UTC)
    age_days = (now - publish_date).days

    if age_days < required_days:
        return QuarantineResult(
            package=package,
            publish_date=publish_date,
            age_days=age_days,
            required_days=required_days,
            is_safe=False,
            risk_level=RiskLevel.QUARANTINE_VIOLATION,
        )

    be_days = bleeding_edge_days if bleeding_edge_days is not None else required_days
    if age_days < be_days:
        return QuarantineResult(
            package=package,
            publish_date=publish_date,
            age_days=age_days,
            required_days=required_days,
            is_safe=True,
            risk_level=RiskLevel.BLEEDING_EDGE,
        )

    return QuarantineResult(
        package=package,
        publish_date=publish_date,
        age_days=age_days,
        required_days=required_days,
        is_safe=True,
        risk_level=RiskLevel.SAFE,
    )


def quarantine_ends(publish_date: datetime, required_days: int) -> datetime:
    """Calculate when the quarantine period ends for a given publish date."""
    return publish_date + timedelta(days=required_days)
