"""Test enrich edge case: error field on quarantine result."""

from datetime import UTC, datetime, timedelta

from sup.models import Ecosystem, PackageInfo, QuarantineResult, RiskLevel
from sup.sbom.enrich import enrich_sbom, _quarantine_properties
from sup.sbom.parse import SbomFormat


def test_quarantine_properties_with_error() -> None:
    pkg = PackageInfo(name="test", version="1.0", ecosystem=Ecosystem.PYTHON)
    result = QuarantineResult(
        package=pkg, publish_date=None, age_days=None,
        required_days=10, is_safe=False,
        risk_level=RiskLevel.UNKNOWN, error="Could not determine publish date",
    )
    props = _quarantine_properties(result, "known", 10)
    prop_names = {p["name"] for p in props}
    assert "sup:quarantine:error" in prop_names
    error_prop = next(p for p in props if p["name"] == "sup:quarantine:error")
    assert error_prop["value"] == "Could not determine publish date"
