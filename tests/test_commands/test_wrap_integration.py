"""Integration tests for sup wrap command — covers all flow paths."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import httpx
import respx
from click.testing import CliRunner

from sup.cli import cli


def _mock_pypi(name: str, version: str, age_days: int) -> None:
    date = (datetime.now(UTC) - timedelta(days=age_days)).isoformat()
    respx.get(f"https://pypi.org/pypi/{name}/json").mock(
        return_value=httpx.Response(
            200, json={"releases": {version: [{"upload_time_iso_8601": date}]}},
        )
    )


@respx.mock
def test_wrap_safe_package(tmp_path: Path) -> None:
    _mock_pypi("requests", "2.31.0", 100)
    with patch("sup.commands.wrap.subprocess") as mock_sub:
        mock_sub.call.return_value = 0
        runner = CliRunner()
        result = runner.invoke(cli, ["wrap", "pip", "install", "requests==2.31.0"])
        assert result.exit_code == 0
        assert "Quarantine check passed" in result.output
        mock_sub.call.assert_called_once()


@respx.mock
def test_wrap_quarantined_blocked(tmp_path: Path) -> None:
    _mock_pypi("newpkg", "1.0.0", 1)
    runner = CliRunner()
    result = runner.invoke(cli, ["wrap", "pip", "install", "newpkg==1.0.0"])
    assert result.exit_code == 1
    assert "Install blocked" in result.output


@respx.mock
def test_wrap_quarantined_warn_only(tmp_path: Path) -> None:
    _mock_pypi("newpkg", "1.0.0", 1)
    with patch("sup.commands.wrap.subprocess") as mock_sub:
        mock_sub.call.return_value = 0
        runner = CliRunner()
        result = runner.invoke(cli, ["wrap", "--warn-only", "pip", "install", "newpkg==1.0.0"])
        assert result.exit_code == 0
        assert "--warn-only" in result.output
        mock_sub.call.assert_called_once()


@respx.mock
def test_wrap_unknown_publish_date() -> None:
    respx.get("https://pypi.org/pypi/mystery/json").mock(
        return_value=httpx.Response(200, json={"releases": {}})
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["wrap", "pip", "install", "mystery==1.0.0"])
    assert result.exit_code == 1
    assert "unknown publish date" in result.output or "Install blocked" in result.output


@respx.mock
def test_wrap_bleeding_edge() -> None:
    _mock_pypi("edgepkg", "1.0.0", 11)
    with patch("sup.commands.wrap.subprocess") as mock_sub:
        mock_sub.call.return_value = 0
        runner = CliRunner()
        result = runner.invoke(cli, ["wrap", "pip", "install", "edgepkg==1.0.0"])
        assert result.exit_code == 0
        assert "bleeding edge" in result.output


def test_wrap_unknown_pm() -> None:
    with patch("sup.commands.wrap.subprocess") as mock_sub:
        mock_sub.call.return_value = 0
        runner = CliRunner()
        result = runner.invoke(cli, ["wrap", "brew", "install", "wget"])
        assert result.exit_code == 0
        assert "Unknown package manager" in result.output


def test_wrap_no_inline_specs() -> None:
    with patch("sup.commands.wrap.subprocess") as mock_sub:
        mock_sub.call.return_value = 0
        runner = CliRunner()
        result = runner.invoke(cli, ["wrap", "pip", "install", "-r", "requirements.txt"])
        assert result.exit_code == 0
        assert "No inline package specs" in result.output
        assert "Tip" in result.output


def test_wrap_no_inline_specs_failure() -> None:
    with patch("sup.commands.wrap.subprocess") as mock_sub:
        mock_sub.call.return_value = 1
        runner = CliRunner()
        result = runner.invoke(cli, ["wrap", "pip", "install", "-r", "requirements.txt"])
        assert result.exit_code == 1
