"""Tests for sup info command."""

from datetime import UTC, datetime, timedelta

import httpx
import respx
from click.testing import CliRunner

from sup.cli import cli


@respx.mock
def test_info_with_version() -> None:
    old_date = (datetime.now(UTC) - timedelta(days=60)).isoformat()
    respx.get("https://pypi.org/pypi/requests/json").mock(
        return_value=httpx.Response(
            200,
            json={"releases": {"2.31.0": [{"upload_time_iso_8601": old_date}]}},
        )
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["info", "requests", "--version", "2.31.0"])
    assert result.exit_code == 0
    assert "requests" in result.output
    assert "60 days" in result.output or "Age" in result.output


@respx.mock
def test_info_version_not_found() -> None:
    respx.get("https://pypi.org/pypi/requests/json").mock(
        return_value=httpx.Response(200, json={"releases": {}})
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["info", "requests", "--version", "99.99.99"])
    assert result.exit_code == 0
    assert "Could not find" in result.output


def test_info_no_version() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["info", "requests"])
    assert result.exit_code == 0
    assert "--version" in result.output
