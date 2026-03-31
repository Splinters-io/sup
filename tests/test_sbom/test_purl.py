"""Tests for purl parsing."""

from sup.models import Ecosystem
from sup.sbom.purl import parse_purl


def test_pypi_purl() -> None:
    result = parse_purl("pkg:pypi/requests@2.31.0")
    assert result is not None
    assert result.type == "pypi"
    assert result.name == "requests"
    assert result.version == "2.31.0"
    assert result.ecosystem == Ecosystem.PYTHON
    assert result.namespace is None


def test_npm_purl() -> None:
    result = parse_purl("pkg:npm/express@4.18.2")
    assert result is not None
    assert result.name == "express"
    assert result.ecosystem == Ecosystem.NODE


def test_npm_scoped_purl() -> None:
    result = parse_purl("pkg:npm/%40angular/core@16.0.0")
    assert result is not None
    assert result.namespace == "@angular"
    assert result.name == "core"
    assert result.version == "16.0.0"
    assert result.ecosystem == Ecosystem.NODE


def test_cargo_purl() -> None:
    result = parse_purl("pkg:cargo/serde@1.0.197")
    assert result is not None
    assert result.name == "serde"
    assert result.ecosystem == Ecosystem.RUST


def test_golang_purl() -> None:
    result = parse_purl("pkg:golang/github.com/gin-gonic/gin@v1.9.1")
    assert result is not None
    assert result.name == "github.com/gin-gonic/gin"
    assert result.version == "v1.9.1"
    assert result.ecosystem == Ecosystem.GO


def test_gem_purl() -> None:
    result = parse_purl("pkg:gem/rails@7.1.2")
    assert result is not None
    assert result.name == "rails"
    assert result.ecosystem == Ecosystem.RUBY


def test_purl_with_qualifiers() -> None:
    result = parse_purl("pkg:pypi/requests@2.31.0?vcs_url=git://github.com")
    assert result is not None
    assert result.name == "requests"
    assert result.version == "2.31.0"


def test_purl_with_subpath() -> None:
    result = parse_purl("pkg:npm/express@4.18.2#src/index.js")
    assert result is not None
    assert result.version == "4.18.2"


def test_invalid_purl() -> None:
    assert parse_purl("not-a-purl") is None
    assert parse_purl("") is None


def test_unknown_type() -> None:
    result = parse_purl("pkg:nuget/Newtonsoft.Json@13.0.1")
    assert result is not None
    assert result.type == "nuget"
    assert result.ecosystem is None


def test_no_version() -> None:
    result = parse_purl("pkg:pypi/requests")
    assert result is not None
    assert result.name == "requests"
    assert result.version is None
