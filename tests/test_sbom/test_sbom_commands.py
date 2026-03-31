"""Tests for sup sbom CLI commands."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import respx
from click.testing import CliRunner

from sup.cli import cli

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _mock_old_pypi(name: str, version: str) -> None:
    old_date = (datetime.now(UTC) - timedelta(days=500)).isoformat()
    respx.get(f"https://pypi.org/pypi/{name}/json").mock(
        return_value=httpx.Response(
            200,
            json={"releases": {version: [{"upload_time_iso_8601": old_date}]}},
        )
    )


def _mock_old_npm(name: str, version: str) -> None:
    old_date = (datetime.now(UTC) - timedelta(days=500)).isoformat()
    respx.get(f"https://registry.npmjs.org/{name}").mock(
        return_value=httpx.Response(200, json={"time": {version: old_date}})
    )


def _mock_old_crates(name: str, version: str) -> None:
    old_date = (datetime.now(UTC) - timedelta(days=500)).isoformat()
    respx.get(f"https://crates.io/api/v1/crates/{name}/versions").mock(
        return_value=httpx.Response(
            200, json={"versions": [{"num": version, "created_at": old_date}]}
        )
    )


def _mock_old_go(module: str, version: str) -> None:
    old_date = (datetime.now(UTC) - timedelta(days=500)).isoformat()
    respx.get(f"https://proxy.golang.org/{module}/@v/{version}.info").mock(
        return_value=httpx.Response(200, json={"Version": version, "Time": old_date})
    )


def _mock_old_gem(name: str, version: str) -> None:
    old_date = (datetime.now(UTC) - timedelta(days=500)).isoformat()
    respx.get(f"https://rubygems.org/api/v1/versions/{name}.json").mock(
        return_value=httpx.Response(
            200, json=[{"number": version, "created_at": old_date}]
        )
    )


@respx.mock
def test_sbom_check_cyclonedx_all_safe() -> None:
    _mock_old_pypi("requests", "2.31.0")
    _mock_old_pypi("flask", "3.0.0")
    _mock_old_npm("express", "4.18.2")
    _mock_old_crates("serde", "1.0.197")
    _mock_old_go("github.com/gin-gonic/gin", "v1.9.1")
    _mock_old_gem("rails", "7.1.2")

    runner = CliRunner()
    result = runner.invoke(cli, ["sbom", "check", str(FIXTURES / "sbom-cyclonedx.json")])
    assert result.exit_code == 0
    assert "passed quarantine" in result.output


@respx.mock
def test_sbom_check_spdx_all_safe() -> None:
    _mock_old_pypi("requests", "2.31.0")
    _mock_old_npm("express", "4.18.2")
    _mock_old_gem("rack", "3.0.8")

    runner = CliRunner()
    result = runner.invoke(cli, ["sbom", "check", str(FIXTURES / "sbom-spdx.json")])
    assert result.exit_code == 0
    assert "passed quarantine" in result.output


@respx.mock
def test_sbom_check_quarantined() -> None:
    new_date = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    respx.get("https://pypi.org/pypi/requests/json").mock(
        return_value=httpx.Response(
            200,
            json={"releases": {"2.31.0": [{"upload_time_iso_8601": new_date}]}},
        )
    )
    _mock_old_pypi("flask", "3.0.0")
    _mock_old_npm("express", "4.18.2")
    _mock_old_crates("serde", "1.0.197")
    _mock_old_go("github.com/gin-gonic/gin", "v1.9.1")
    _mock_old_gem("rails", "7.1.2")

    runner = CliRunner()
    result = runner.invoke(cli, ["sbom", "check", str(FIXTURES / "sbom-cyclonedx.json")])
    assert result.exit_code == 1
    assert "QUARANTINE" in result.output


@respx.mock
def test_sbom_enrich_cyclonedx(tmp_path: Path) -> None:
    _mock_old_pypi("requests", "2.31.0")
    _mock_old_pypi("flask", "3.0.0")
    _mock_old_npm("express", "4.18.2")
    _mock_old_crates("serde", "1.0.197")
    _mock_old_go("github.com/gin-gonic/gin", "v1.9.1")
    _mock_old_gem("rails", "7.1.2")

    output_path = tmp_path / "enriched.json"
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["sbom", "enrich", str(FIXTURES / "sbom-cyclonedx.json"), "-o", str(output_path)],
    )
    assert result.exit_code == 0
    assert output_path.exists()

    enriched = json.loads(output_path.read_text())
    assert enriched["bomFormat"] == "CycloneDX"

    # Check properties were added
    requests_comp = next(
        c for c in enriched["components"] if c["name"] == "requests"
    )
    prop_names = {p["name"] for p in requests_comp.get("properties", [])}
    assert "sup:quarantine:status" in prop_names
    assert "sup:quarantine:age_days" in prop_names

    # Check tool metadata
    tool_names = {t["name"] for t in enriched["metadata"]["tools"]}
    assert "sup-quarantine" in tool_names


@respx.mock
def test_sbom_enrich_spdx(tmp_path: Path) -> None:
    _mock_old_pypi("requests", "2.31.0")
    _mock_old_npm("express", "4.18.2")
    _mock_old_gem("rack", "3.0.8")

    output_path = tmp_path / "enriched.json"
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["sbom", "enrich", str(FIXTURES / "sbom-spdx.json"), "-o", str(output_path)],
    )
    assert result.exit_code == 0
    assert output_path.exists()

    enriched = json.loads(output_path.read_text())
    assert enriched["spdxVersion"] == "SPDX-2.3"
    assert len(enriched["annotations"]) == 3
    assert "Tool: sup-quarantine-0.1.0" in enriched["creationInfo"]["creators"]


def test_sbom_check_invalid_file(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text('{"not": "an sbom"}')
    runner = CliRunner()
    result = runner.invoke(cli, ["sbom", "check", str(bad)])
    assert result.exit_code == 1
    assert "Unrecognised SBOM format" in result.output


@respx.mock
def test_sbom_report_generates_text(tmp_path: Path) -> None:
    _mock_old_pypi("requests", "2.31.0")
    _mock_old_pypi("flask", "3.0.0")
    _mock_old_npm("express", "4.18.2")
    _mock_old_crates("serde", "1.0.197")
    _mock_old_go("github.com/gin-gonic/gin", "v1.9.1")
    _mock_old_gem("rails", "7.1.2")

    runner = CliRunner()
    result = runner.invoke(
        cli, ["sbom", "report", str(FIXTURES / "sbom-cyclonedx.json")]
    )
    assert result.exit_code == 0
    assert "Supply Chain Quarantine Report" in result.output
    assert "VERDICT: PASS" in result.output
    assert "Safe Components" in result.output


@respx.mock
def test_sbom_report_with_violation(tmp_path: Path) -> None:
    new_date = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    respx.get("https://pypi.org/pypi/requests/json").mock(
        return_value=httpx.Response(
            200,
            json={"releases": {"2.31.0": [{"upload_time_iso_8601": new_date}]}},
        )
    )
    _mock_old_pypi("flask", "3.0.0")
    _mock_old_npm("express", "4.18.2")
    _mock_old_crates("serde", "1.0.197")
    _mock_old_go("github.com/gin-gonic/gin", "v1.9.1")
    _mock_old_gem("rails", "7.1.2")

    runner = CliRunner()
    result = runner.invoke(
        cli, ["sbom", "report", str(FIXTURES / "sbom-cyclonedx.json")]
    )
    assert result.exit_code == 0
    assert "VERDICT: FAIL" in result.output
    assert "Quarantine Violations" in result.output
    assert "requests" in result.output


@respx.mock
def test_sbom_report_to_file(tmp_path: Path) -> None:
    _mock_old_pypi("requests", "2.31.0")
    _mock_old_pypi("flask", "3.0.0")
    _mock_old_npm("express", "4.18.2")
    _mock_old_crates("serde", "1.0.197")
    _mock_old_go("github.com/gin-gonic/gin", "v1.9.1")
    _mock_old_gem("rails", "7.1.2")

    report_path = tmp_path / "report.md"
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["sbom", "report", str(FIXTURES / "sbom-cyclonedx.json"), "-o", str(report_path)],
    )
    assert result.exit_code == 0
    assert report_path.exists()
    content = report_path.read_text()
    assert "Supply Chain Quarantine Report" in content
    assert "VERDICT: PASS" in content


@respx.mock
def test_sbom_report_bleeding_edge() -> None:
    """Package at 11 days with known=10, bleeding_edge=14 -> flagged in report."""
    eleven_days = (datetime.now(UTC) - timedelta(days=11)).isoformat()
    respx.get("https://pypi.org/pypi/requests/json").mock(
        return_value=httpx.Response(
            200,
            json={"releases": {"2.31.0": [{"upload_time_iso_8601": eleven_days}]}},
        )
    )
    _mock_old_pypi("flask", "3.0.0")
    _mock_old_npm("express", "4.18.2")
    _mock_old_crates("serde", "1.0.197")
    _mock_old_go("github.com/gin-gonic/gin", "v1.9.1")
    _mock_old_gem("rails", "7.1.2")

    runner = CliRunner()
    result = runner.invoke(
        cli, ["sbom", "report", str(FIXTURES / "sbom-cyclonedx.json")]
    )
    assert result.exit_code == 0
    assert "Bleeding Edge Components" in result.output
    assert "VERDICT: PASS with" in result.output
