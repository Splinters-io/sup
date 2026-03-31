"""Tests for sup check command."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import httpx
import respx
from click.testing import CliRunner

from sup.cli import cli

FIXTURES = Path(__file__).parent.parent / "fixtures"


@respx.mock
def test_check_with_safe_packages(tmp_path: Path) -> None:
    """All packages old enough — should exit 0."""
    (tmp_path / "requirements.txt").write_text("requests==2.31.0\n")

    old_date = (datetime.now(UTC) - timedelta(days=30)).isoformat()
    respx.get("https://pypi.org/pypi/requests/json").mock(
        return_value=httpx.Response(
            200,
            json={"releases": {"2.31.0": [{"upload_time_iso_8601": old_date}]}},
        )
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["check", "--dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "safe" in result.output or "passed quarantine" in result.output


@respx.mock
def test_check_with_quarantined_packages(tmp_path: Path) -> None:
    """Package published yesterday — should exit 1."""
    (tmp_path / "requirements.txt").write_text("newpkg==1.0.0\n")

    yesterday = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    respx.get("https://pypi.org/pypi/newpkg/json").mock(
        return_value=httpx.Response(
            200,
            json={"releases": {"1.0.0": [{"upload_time_iso_8601": yesterday}]}},
        )
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["check", "--dir", str(tmp_path)])
    assert result.exit_code == 1
    assert "QUARANTINE" in result.output


@respx.mock
def test_check_warn_only(tmp_path: Path) -> None:
    """With --warn-only, should exit 0 even with quarantined packages."""
    (tmp_path / "requirements.txt").write_text("newpkg==1.0.0\n")

    yesterday = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    respx.get("https://pypi.org/pypi/newpkg/json").mock(
        return_value=httpx.Response(
            200,
            json={"releases": {"1.0.0": [{"upload_time_iso_8601": yesterday}]}},
        )
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["check", "--dir", str(tmp_path), "--warn-only"])
    assert result.exit_code == 0
    assert "Warning" in result.output


@respx.mock
def test_check_bleeding_edge_tier(tmp_path: Path) -> None:
    """Package at 11 days — safe for known, quarantined for bleeding_edge."""
    (tmp_path / "requirements.txt").write_text("somepkg==2.0.0\n")

    eleven_days_ago = (datetime.now(UTC) - timedelta(days=11)).isoformat()
    respx.get("https://pypi.org/pypi/somepkg/json").mock(
        return_value=httpx.Response(
            200,
            json={"releases": {"2.0.0": [{"upload_time_iso_8601": eleven_days_ago}]}},
        )
    )

    runner = CliRunner()
    result = runner.invoke(
        cli, ["check", "--dir", str(tmp_path), "--tier", "bleeding_edge"]
    )
    assert result.exit_code == 1
    assert "QUARANTINE" in result.output


def test_check_no_dependency_files(tmp_path: Path) -> None:
    """Empty directory — should exit 1 with error message."""
    runner = CliRunner()
    result = runner.invoke(cli, ["check", "--dir", str(tmp_path)])
    assert result.exit_code == 1
    assert "No supported dependency files" in result.output
