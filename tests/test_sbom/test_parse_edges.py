"""Tests for SBOM parse edge cases — components without version, without purl, SPDX without purl, etc."""

import json
from pathlib import Path

from sup.models import Ecosystem
from sup.sbom.parse import parse_sbom


def test_cyclonedx_component_without_version(tmp_path: Path) -> None:
    sbom = {
        "bomFormat": "CycloneDX", "specVersion": "1.5",
        "components": [
            {"type": "library", "name": "noversion", "purl": "pkg:pypi/noversion@1.0"},
            {"type": "library", "name": "hasversion", "version": "1.0", "purl": "pkg:pypi/hasversion@1.0"},
        ],
    }
    p = tmp_path / "sbom.json"
    p.write_text(json.dumps(sbom))
    _fmt, packages, _raw = parse_sbom(p)
    assert len(packages) == 1
    assert packages[0].name == "hasversion"


def test_cyclonedx_component_without_purl(tmp_path: Path) -> None:
    """Component with no purl and no properties — should be skipped."""
    sbom = {
        "bomFormat": "CycloneDX", "specVersion": "1.5",
        "components": [
            {"type": "library", "name": "nopurl", "version": "1.0"},
        ],
    }
    p = tmp_path / "sbom.json"
    p.write_text(json.dumps(sbom))
    _fmt, packages, _raw = parse_sbom(p)
    assert len(packages) == 0


def test_cyclonedx_component_with_npm_property(tmp_path: Path) -> None:
    """Component without purl but with npm property hint."""
    sbom = {
        "bomFormat": "CycloneDX", "specVersion": "1.5",
        "components": [
            {
                "type": "library", "name": "express", "version": "4.18.2",
                "properties": [{"name": "cdx:npm:package:type", "value": "library"}],
            },
        ],
    }
    p = tmp_path / "sbom.json"
    p.write_text(json.dumps(sbom))
    _fmt, packages, _raw = parse_sbom(p)
    assert len(packages) == 1
    assert packages[0].ecosystem == Ecosystem.NODE


def test_spdx_package_without_version(tmp_path: Path) -> None:
    sbom = {
        "spdxVersion": "SPDX-2.3",
        "packages": [
            {"name": "noversion", "SPDXID": "SPDXRef-1",
             "externalRefs": [{"referenceType": "purl", "referenceLocator": "pkg:pypi/noversion@1.0"}]},
        ],
    }
    p = tmp_path / "sbom.json"
    p.write_text(json.dumps(sbom))
    _fmt, packages, _raw = parse_sbom(p)
    assert len(packages) == 0


def test_spdx_package_without_purl(tmp_path: Path) -> None:
    sbom = {
        "spdxVersion": "SPDX-2.3",
        "packages": [
            {"name": "nopurl", "versionInfo": "1.0", "SPDXID": "SPDXRef-1"},
        ],
    }
    p = tmp_path / "sbom.json"
    p.write_text(json.dumps(sbom))
    _fmt, packages, _raw = parse_sbom(p)
    assert len(packages) == 0


def test_spdx_go_package(tmp_path: Path) -> None:
    """SPDX package with golang purl — name should be the full module path."""
    sbom = {
        "spdxVersion": "SPDX-2.3",
        "packages": [
            {
                "name": "gin", "versionInfo": "v1.9.1", "SPDXID": "SPDXRef-1",
                "externalRefs": [{"referenceType": "purl", "referenceLocator": "pkg:golang/github.com/gin-gonic/gin@v1.9.1"}],
            },
        ],
    }
    p = tmp_path / "sbom.json"
    p.write_text(json.dumps(sbom))
    _fmt, packages, _raw = parse_sbom(p)
    assert len(packages) == 1
    assert packages[0].name == "github.com/gin-gonic/gin"
    assert packages[0].ecosystem == Ecosystem.GO


def test_sbom_file_too_large(tmp_path: Path) -> None:
    import pytest
    p = tmp_path / "huge.json"
    p.write_text('{"bomFormat": "CycloneDX"}' + " " * (51 * 1024 * 1024))
    with pytest.raises(ValueError, match="exceeds"):
        parse_sbom(p)


def test_sbom_invalid_json(tmp_path: Path) -> None:
    import pytest
    p = tmp_path / "bad.json"
    p.write_text("not json {{{")
    with pytest.raises(ValueError, match="Invalid JSON"):
        parse_sbom(p)
