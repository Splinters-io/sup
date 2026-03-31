"""Tests for SBOM command edge cases — enrich error, report unknown, bleeding edge summary."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import respx
from click.testing import CliRunner

from sup.cli import cli

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _mock_pypi(name: str, version: str, age_days: int) -> None:
    date = (datetime.now(UTC) - timedelta(days=age_days)).isoformat()
    respx.get(f"https://pypi.org/pypi/{name}/json").mock(
        return_value=httpx.Response(200, json={"releases": {version: [{"upload_time_iso_8601": date}]}})
    )


def _mock_npm(name: str, version: str, age_days: int) -> None:
    date = (datetime.now(UTC) - timedelta(days=age_days)).isoformat()
    respx.get(f"https://registry.npmjs.org/{name}").mock(
        return_value=httpx.Response(200, json={"time": {version: date}})
    )


def _mock_crates(name: str, version: str, age_days: int) -> None:
    date = (datetime.now(UTC) - timedelta(days=age_days)).isoformat()
    respx.get(f"https://crates.io/api/v1/crates/{name}/versions").mock(
        return_value=httpx.Response(200, json={"versions": [{"num": version, "created_at": date}]})
    )


def _mock_go(module: str, version: str, age_days: int) -> None:
    date = (datetime.now(UTC) - timedelta(days=age_days)).isoformat()
    respx.get(f"https://proxy.golang.org/{module}/@v/{version}.info").mock(
        return_value=httpx.Response(200, json={"Version": version, "Time": date})
    )


def _mock_gem(name: str, version: str, age_days: int) -> None:
    date = (datetime.now(UTC) - timedelta(days=age_days)).isoformat()
    respx.get(f"https://rubygems.org/api/v1/versions/{name}.json").mock(
        return_value=httpx.Response(200, json=[{"number": version, "created_at": date}])
    )


def _mock_all_old() -> None:
    _mock_pypi("requests", "2.31.0", 500)
    _mock_pypi("flask", "3.0.0", 500)
    _mock_npm("express", "4.18.2", 500)
    _mock_crates("serde", "1.0.197", 500)
    _mock_go("github.com/gin-gonic/gin", "v1.9.1", 500)
    _mock_gem("rails", "7.1.2", 500)


@respx.mock
def test_sbom_enrich_error_path(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text('{"not": "sbom"}')
    runner = CliRunner()
    result = runner.invoke(cli, ["sbom", "enrich", str(bad)])
    assert result.exit_code == 1
    assert "Unrecognised" in result.output


@respx.mock
def test_sbom_check_unknown_package() -> None:
    """SBOM with a package whose publish date can't be determined."""
    respx.get("https://pypi.org/pypi/requests/json").mock(
        return_value=httpx.Response(200, json={"releases": {}})
    )
    _mock_pypi("flask", "3.0.0", 500)
    _mock_npm("express", "4.18.2", 500)
    _mock_crates("serde", "1.0.197", 500)
    _mock_go("github.com/gin-gonic/gin", "v1.9.1", 500)
    _mock_gem("rails", "7.1.2", 500)

    runner = CliRunner()
    result = runner.invoke(cli, ["sbom", "check", str(FIXTURES / "sbom-cyclonedx.json")])
    assert result.exit_code == 1
    assert "could not verify" in result.output or "unknown" in result.output.lower()


@respx.mock
def test_sbom_check_warn_only_with_violation() -> None:
    _mock_pypi("requests", "2.31.0", 1)  # too new
    _mock_pypi("flask", "3.0.0", 500)
    _mock_npm("express", "4.18.2", 500)
    _mock_crates("serde", "1.0.197", 500)
    _mock_go("github.com/gin-gonic/gin", "v1.9.1", 500)
    _mock_gem("rails", "7.1.2", 500)

    runner = CliRunner()
    result = runner.invoke(cli, ["sbom", "check", str(FIXTURES / "sbom-cyclonedx.json"), "--warn-only"])
    assert result.exit_code == 0
    assert "Warning" in result.output


@respx.mock
def test_sbom_check_bleeding_edge() -> None:
    _mock_pypi("requests", "2.31.0", 11)  # between known(10) and bleeding(14)
    _mock_pypi("flask", "3.0.0", 500)
    _mock_npm("express", "4.18.2", 500)
    _mock_crates("serde", "1.0.197", 500)
    _mock_go("github.com/gin-gonic/gin", "v1.9.1", 500)
    _mock_gem("rails", "7.1.2", 500)

    runner = CliRunner()
    result = runner.invoke(cli, ["sbom", "check", str(FIXTURES / "sbom-cyclonedx.json")])
    assert result.exit_code == 0
    assert "bleeding edge" in result.output


@respx.mock
def test_sbom_enrich_with_mixed_results(tmp_path: Path) -> None:
    _mock_pypi("requests", "2.31.0", 11)  # bleeding edge
    _mock_pypi("flask", "3.0.0", 1)  # violation
    _mock_npm("express", "4.18.2", 500)
    _mock_crates("serde", "1.0.197", 500)
    _mock_go("github.com/gin-gonic/gin", "v1.9.1", 500)
    _mock_gem("rails", "7.1.2", 500)

    output = tmp_path / "enriched.json"
    runner = CliRunner()
    result = runner.invoke(cli, [
        "sbom", "enrich", str(FIXTURES / "sbom-cyclonedx.json"), "-o", str(output),
    ])
    assert result.exit_code == 0
    assert "Bleeding edge" in result.output
    assert "Quarantine violations" in result.output


@respx.mock
def test_sbom_report_unknown_verdict() -> None:
    respx.get("https://pypi.org/pypi/requests/json").mock(
        return_value=httpx.Response(200, json={"releases": {}})
    )
    _mock_pypi("flask", "3.0.0", 500)
    _mock_npm("express", "4.18.2", 500)
    _mock_crates("serde", "1.0.197", 500)
    _mock_go("github.com/gin-gonic/gin", "v1.9.1", 500)
    _mock_gem("rails", "7.1.2", 500)

    runner = CliRunner()
    result = runner.invoke(cli, ["sbom", "report", str(FIXTURES / "sbom-cyclonedx.json")])
    assert result.exit_code == 0
    assert "Unverifiable" in result.output
    assert "VERDICT: FAIL" in result.output


@respx.mock
def test_sbom_report_error_path(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text('{"not": "sbom"}')
    runner = CliRunner()
    result = runner.invoke(cli, ["sbom", "report", str(bad)])
    assert result.exit_code == 1
