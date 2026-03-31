"""Tests for SBOM parsing."""

from pathlib import Path

import pytest

from sup.models import Ecosystem
from sup.sbom.parse import SbomFormat, detect_sbom_format, parse_sbom

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_detect_cyclonedx() -> None:
    data = {"bomFormat": "CycloneDX", "specVersion": "1.5"}
    assert detect_sbom_format(data) == SbomFormat.CYCLONEDX


def test_detect_spdx() -> None:
    data = {"spdxVersion": "SPDX-2.3"}
    assert detect_sbom_format(data) == SbomFormat.SPDX


def test_detect_unknown() -> None:
    assert detect_sbom_format({"foo": "bar"}) is None


def test_parse_cyclonedx() -> None:
    fmt, packages, raw = parse_sbom(FIXTURES / "sbom-cyclonedx.json")
    assert fmt == SbomFormat.CYCLONEDX
    assert len(packages) == 6

    names = {p.name for p in packages}
    assert "requests" in names
    assert "express" in names
    assert "serde" in names
    assert "github.com/gin-gonic/gin" in names
    assert "rails" in names

    ecosystems = {p.ecosystem for p in packages}
    assert Ecosystem.PYTHON in ecosystems
    assert Ecosystem.NODE in ecosystems
    assert Ecosystem.RUST in ecosystems
    assert Ecosystem.GO in ecosystems
    assert Ecosystem.RUBY in ecosystems


def test_parse_spdx() -> None:
    fmt, packages, raw = parse_sbom(FIXTURES / "sbom-spdx.json")
    assert fmt == SbomFormat.SPDX
    assert len(packages) == 3

    names = {p.name for p in packages}
    assert "requests" in names
    assert "express" in names
    assert "rack" in names


def test_parse_cyclonedx_preserves_raw() -> None:
    _fmt, _packages, raw = parse_sbom(FIXTURES / "sbom-cyclonedx.json")
    assert raw["bomFormat"] == "CycloneDX"
    assert "components" in raw


def test_parse_spdx_preserves_raw() -> None:
    _fmt, _packages, raw = parse_sbom(FIXTURES / "sbom-spdx.json")
    assert raw["spdxVersion"] == "SPDX-2.3"
    assert "packages" in raw


def test_parse_invalid_format(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text('{"not": "an sbom"}')
    with pytest.raises(ValueError, match="Unrecognised SBOM format"):
        parse_sbom(bad)
