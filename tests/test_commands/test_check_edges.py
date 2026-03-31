"""Tests for sup check edge cases — no-cache, bleeding edge, unknown exit paths."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import respx
from click.testing import CliRunner

from sup.cli import cli


@respx.mock
def test_check_no_cache_flag(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("requests==2.31.0\n")
    old = (datetime.now(UTC) - timedelta(days=100)).isoformat()
    respx.get("https://pypi.org/pypi/requests/json").mock(
        return_value=httpx.Response(200, json={"releases": {"2.31.0": [{"upload_time_iso_8601": old}]}})
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["check", "--dir", str(tmp_path), "--no-cache"])
    assert result.exit_code == 0


@respx.mock
def test_check_unknown_blocks(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("mystery==1.0.0\n")
    respx.get("https://pypi.org/pypi/mystery/json").mock(
        return_value=httpx.Response(200, json={"releases": {}})
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["check", "--dir", str(tmp_path), "--no-cache"])
    assert result.exit_code == 1
    assert "could not be verified" in result.output


@respx.mock
def test_check_bleeding_edge_shown(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("edgepkg==1.0.0\n")
    eleven_days = (datetime.now(UTC) - timedelta(days=11)).isoformat()
    respx.get("https://pypi.org/pypi/edgepkg/json").mock(
        return_value=httpx.Response(200, json={"releases": {"1.0.0": [{"upload_time_iso_8601": eleven_days}]}})
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["check", "--dir", str(tmp_path), "--no-cache"])
    assert result.exit_code == 0
    assert "bleeding edge" in result.output


def test_check_empty_deps(tmp_path: Path) -> None:
    """Project with a requirements.txt that has no pinned deps."""
    (tmp_path / "requirements.txt").write_text("# just a comment\n")
    runner = CliRunner()
    result = runner.invoke(cli, ["check", "--dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "No dependencies found" in result.output


@respx.mock
def test_check_warn_only_with_unknown(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("mystery==1.0.0\n")
    respx.get("https://pypi.org/pypi/mystery/json").mock(
        return_value=httpx.Response(200, json={"releases": {}})
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["check", "--dir", str(tmp_path), "--warn-only", "--no-cache"])
    assert result.exit_code == 0
