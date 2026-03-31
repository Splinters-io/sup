"""Tests for core quarantine evaluation logic."""

from datetime import UTC, datetime, timedelta

from sup.models import Ecosystem, PackageInfo, RiskLevel
from sup.quarantine import evaluate, quarantine_ends


def _make_package(name: str = "test-pkg", version: str = "1.0.0") -> PackageInfo:
    return PackageInfo(name=name, version=version, ecosystem=Ecosystem.PYTHON)


def test_safe_package() -> None:
    """Package published 30 days ago should be safe with 10-day threshold."""
    pkg = _make_package()
    publish_date = datetime.now(UTC) - timedelta(days=30)
    result = evaluate(pkg, publish_date, required_days=10, bleeding_edge_days=14)
    assert result.is_safe is True
    assert result.risk_level == RiskLevel.SAFE
    assert result.age_days == 30
    assert result.error is None


def test_quarantined_package() -> None:
    """Package published 3 days ago should be a quarantine violation."""
    pkg = _make_package()
    publish_date = datetime.now(UTC) - timedelta(days=3)
    result = evaluate(pkg, publish_date, required_days=10, bleeding_edge_days=14)
    assert result.is_safe is False
    assert result.risk_level == RiskLevel.QUARANTINE_VIOLATION
    assert result.age_days == 3
    assert result.required_days == 10


def test_exact_threshold() -> None:
    """Package exactly at known threshold but below bleeding edge -> bleeding edge."""
    pkg = _make_package()
    publish_date = datetime.now(UTC) - timedelta(days=10)
    result = evaluate(pkg, publish_date, required_days=10, bleeding_edge_days=14)
    assert result.is_safe is True
    assert result.risk_level == RiskLevel.BLEEDING_EDGE


def test_unknown_publish_date() -> None:
    """None publish_date should result in UNKNOWN risk."""
    pkg = _make_package()
    result = evaluate(pkg, None, required_days=10)
    assert result.is_safe is False
    assert result.risk_level == RiskLevel.UNKNOWN
    assert result.age_days is None
    assert result.error is not None


def test_bleeding_edge_classification() -> None:
    """Package at 11 days with known=10, bleeding_edge=14 -> BLEEDING_EDGE."""
    pkg = _make_package()
    publish_date = datetime.now(UTC) - timedelta(days=11)
    result = evaluate(pkg, publish_date, required_days=10, bleeding_edge_days=14)
    assert result.is_safe is True
    assert result.risk_level == RiskLevel.BLEEDING_EDGE


def test_past_bleeding_edge_is_safe() -> None:
    """Package at 15 days with known=10, bleeding_edge=14 -> SAFE."""
    pkg = _make_package()
    publish_date = datetime.now(UTC) - timedelta(days=15)
    result = evaluate(pkg, publish_date, required_days=10, bleeding_edge_days=14)
    assert result.is_safe is True
    assert result.risk_level == RiskLevel.SAFE


def test_no_bleeding_edge_days_defaults_to_required() -> None:
    """When bleeding_edge_days not provided, no bleeding edge window."""
    pkg = _make_package()
    publish_date = datetime.now(UTC) - timedelta(days=10)
    result = evaluate(pkg, publish_date, required_days=10)
    assert result.is_safe is True
    assert result.risk_level == RiskLevel.SAFE


def test_quarantine_ends_calculation() -> None:
    publish_date = datetime(2024, 1, 1, tzinfo=UTC)
    end = quarantine_ends(publish_date, 10)
    assert end == datetime(2024, 1, 11, tzinfo=UTC)


def test_result_is_immutable() -> None:
    """QuarantineResult should be frozen."""
    pkg = _make_package()
    result = evaluate(pkg, datetime.now(UTC), required_days=10)
    try:
        result.is_safe = True  # type: ignore[misc]
        assert False, "Should have raised FrozenInstanceError"
    except AttributeError:
        pass
