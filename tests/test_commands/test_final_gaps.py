"""Final coverage gap tests."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import respx
from click.testing import CliRunner

from sup.cli import cli
from sup.commands.wrap import _parse_package_spec
from sup.models import Ecosystem


# --- check.py:73 — --type flag ---

@respx.mock
def test_check_with_type_flag(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("requests==2.31.0\n")
    old = (datetime.now(UTC) - timedelta(days=100)).isoformat()
    respx.get("https://pypi.org/pypi/requests/json").mock(
        return_value=httpx.Response(200, json={"releases": {"2.31.0": [{"upload_time_iso_8601": old}]}})
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["check", "--dir", str(tmp_path), "--type", "python", "--no-cache"])
    assert result.exit_code == 0


# --- wrap.py: Rust/Go/Ruby parse paths ---


def test_parse_cargo_no_version() -> None:
    assert _parse_package_spec("serde", Ecosystem.RUST) is None


def test_parse_go_no_version() -> None:
    assert _parse_package_spec("github.com/foo/bar", Ecosystem.GO) is None


def test_parse_ruby_spec() -> None:
    assert _parse_package_spec("rails", Ecosystem.RUBY) is None


def test_parse_npm_no_version() -> None:
    assert _parse_package_spec("express", Ecosystem.NODE) is None


def test_parse_unknown_ecosystem() -> None:
    # If somehow an unrecognised ecosystem reaches the parser
    # Using PYTHON but with a non-matching spec
    assert _parse_package_spec("notpinned", Ecosystem.PYTHON) is None


# --- sbom enrich with unknown ---


@respx.mock
def test_sbom_enrich_with_unknown(tmp_path: Path) -> None:
    FIXTURES = Path(__file__).parent.parent / "fixtures"
    # requests will be unknown
    respx.get("https://pypi.org/pypi/requests/json").mock(
        return_value=httpx.Response(200, json={"releases": {}})
    )
    old = (datetime.now(UTC) - timedelta(days=500)).isoformat()
    respx.get("https://pypi.org/pypi/flask/json").mock(
        return_value=httpx.Response(200, json={"releases": {"3.0.0": [{"upload_time_iso_8601": old}]}})
    )
    respx.get("https://registry.npmjs.org/express").mock(
        return_value=httpx.Response(200, json={"time": {"4.18.2": old}})
    )
    respx.get("https://crates.io/api/v1/crates/serde/versions").mock(
        return_value=httpx.Response(200, json={"versions": [{"num": "1.0.197", "created_at": old}]})
    )
    respx.get("https://proxy.golang.org/github.com/gin-gonic/gin/@v/v1.9.1.info").mock(
        return_value=httpx.Response(200, json={"Version": "v1.9.1", "Time": old})
    )
    respx.get("https://rubygems.org/api/v1/versions/rails.json").mock(
        return_value=httpx.Response(200, json=[{"number": "7.1.2", "created_at": old}])
    )

    output = tmp_path / "enriched.json"
    runner = CliRunner()
    result = runner.invoke(cli, [
        "sbom", "enrich", str(FIXTURES / "sbom-cyclonedx.json"), "-o", str(output),
    ])
    assert result.exit_code == 0
    assert "Unknown" in result.output
