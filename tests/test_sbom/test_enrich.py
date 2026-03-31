"""Tests for SBOM enrichment."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from sup.models import Ecosystem, PackageInfo, QuarantineResult, RiskLevel
from sup.sbom.enrich import enrich_sbom
from sup.sbom.parse import SbomFormat, parse_sbom

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _make_result(
    name: str,
    version: str,
    ecosystem: Ecosystem,
    is_safe: bool,
    age_days: int = 100,
    risk_level: RiskLevel = RiskLevel.SAFE,
) -> QuarantineResult:
    pkg = PackageInfo(name=name, version=version, ecosystem=ecosystem)
    publish_date = datetime.now(UTC) - timedelta(days=age_days)
    return QuarantineResult(
        package=pkg,
        publish_date=publish_date,
        age_days=age_days,
        required_days=10,
        is_safe=is_safe,
        risk_level=risk_level,
    )


def test_enrich_cyclonedx_adds_properties() -> None:
    _fmt, _packages, raw = parse_sbom(FIXTURES / "sbom-cyclonedx.json")

    results = [
        _make_result("requests", "2.31.0", Ecosystem.PYTHON, True, 1043),
        _make_result("flask", "3.0.0", Ecosystem.PYTHON, True, 912),
    ]

    enriched = enrich_sbom(raw, SbomFormat.CYCLONEDX, results, "known", 10)

    # Original not mutated
    assert "properties" not in raw["components"][0]

    # Find enriched requests component
    requests_comp = next(
        c for c in enriched["components"] if c["name"] == "requests"
    )
    props = requests_comp["properties"]
    prop_names = {p["name"] for p in props}
    assert "sup:quarantine:status" in prop_names
    assert "sup:quarantine:tier" in prop_names
    assert "sup:quarantine:age_days" in prop_names
    assert "sup:quarantine:publish_date" in prop_names

    status_prop = next(p for p in props if p["name"] == "sup:quarantine:status")
    assert status_prop["value"] == "safe"


def test_enrich_cyclonedx_quarantined_status() -> None:
    _fmt, _packages, raw = parse_sbom(FIXTURES / "sbom-cyclonedx.json")

    results = [
        _make_result("requests", "2.31.0", Ecosystem.PYTHON, False, 3, RiskLevel.QUARANTINE_VIOLATION),
    ]

    enriched = enrich_sbom(raw, SbomFormat.CYCLONEDX, results, "known", 10)

    requests_comp = next(
        c for c in enriched["components"] if c["name"] == "requests"
    )
    status_prop = next(
        p for p in requests_comp["properties"]
        if p["name"] == "sup:quarantine:status"
    )
    assert status_prop["value"] == "quarantine_violation"


def test_enrich_cyclonedx_adds_tool_metadata() -> None:
    _fmt, _packages, raw = parse_sbom(FIXTURES / "sbom-cyclonedx.json")
    enriched = enrich_sbom(raw, SbomFormat.CYCLONEDX, [], "known", 10)

    tools = enriched["metadata"]["tools"]
    tool_names = {t["name"] for t in tools}
    assert "sup-quarantine" in tool_names


def test_enrich_spdx_adds_annotations() -> None:
    _fmt, _packages, raw = parse_sbom(FIXTURES / "sbom-spdx.json")

    results = [
        _make_result("requests", "2.31.0", Ecosystem.PYTHON, True, 1043),
        _make_result("express", "4.18.2", Ecosystem.NODE, True, 1269),
    ]

    enriched = enrich_sbom(raw, SbomFormat.SPDX, results, "known", 10)

    # Original not mutated
    assert "annotations" not in raw

    annotations = enriched["annotations"]
    assert len(annotations) == 2

    comments = [a["comment"] for a in annotations]
    assert any("status=safe" in c for c in comments)
    assert all(a["annotationType"] == "REVIEW" for a in annotations)
    assert all("sup-quarantine" in a["annotator"] for a in annotations)


def test_enrich_spdx_adds_creator() -> None:
    _fmt, _packages, raw = parse_sbom(FIXTURES / "sbom-spdx.json")
    enriched = enrich_sbom(raw, SbomFormat.SPDX, [], "known", 10)

    creators = enriched["creationInfo"]["creators"]
    assert "Tool: sup-quarantine-0.1.0" in creators


def test_enrich_does_not_mutate_original() -> None:
    _fmt, _packages, raw = parse_sbom(FIXTURES / "sbom-cyclonedx.json")
    original_components = len(raw["components"])

    results = [
        _make_result("requests", "2.31.0", Ecosystem.PYTHON, True),
    ]
    enrich_sbom(raw, SbomFormat.CYCLONEDX, results, "known", 10)

    # raw unchanged
    assert len(raw["components"]) == original_components
    assert "properties" not in raw["components"][0]
