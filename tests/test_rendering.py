"""Tests for shared rendering helpers — covers all RiskLevel branches."""

from datetime import UTC, datetime, timedelta

from sup.commands.rendering import format_risk
from sup.models import Ecosystem, PackageInfo, QuarantineResult, RiskLevel


def _pkg() -> PackageInfo:
    return PackageInfo(name="test", version="1.0", ecosystem=Ecosystem.PYTHON)


def test_format_safe() -> None:
    r = QuarantineResult(
        package=_pkg(), publish_date=datetime.now(UTC) - timedelta(days=30),
        age_days=30, required_days=10, is_safe=True, risk_level=RiskLevel.SAFE,
    )
    risk, status = format_risk(r)
    assert "low" in risk
    assert "safe" in status


def test_format_bleeding_edge() -> None:
    r = QuarantineResult(
        package=_pkg(), publish_date=datetime.now(UTC) - timedelta(days=11),
        age_days=11, required_days=10, is_safe=True, risk_level=RiskLevel.BLEEDING_EDGE,
    )
    risk, status = format_risk(r)
    assert "elevated" in risk
    assert "bleeding edge" in status


def test_format_quarantine_violation() -> None:
    r = QuarantineResult(
        package=_pkg(), publish_date=datetime.now(UTC) - timedelta(days=3),
        age_days=3, required_days=10, is_safe=False, risk_level=RiskLevel.QUARANTINE_VIOLATION,
    )
    risk, status = format_risk(r)
    assert "high" in risk
    assert "QUARANTINE VIOLATION" in status


def test_format_unknown() -> None:
    r = QuarantineResult(
        package=_pkg(), publish_date=None,
        age_days=None, required_days=10, is_safe=False,
        risk_level=RiskLevel.UNKNOWN, error="Could not determine publish date",
    )
    risk, status = format_risk(r)
    assert "unknown" in risk
    assert "Could not determine" in status


def test_format_unknown_no_error() -> None:
    r = QuarantineResult(
        package=_pkg(), publish_date=None,
        age_days=None, required_days=10, is_safe=False,
        risk_level=RiskLevel.UNKNOWN, error=None,
    )
    _risk, status = format_risk(r)
    assert "unknown" in status
