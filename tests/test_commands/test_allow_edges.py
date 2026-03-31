"""Tests for sup allow command — list with entries, remove success."""

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from sup.allowlist import AllowlistEntry
from sup.cli import cli


def test_allow_list_with_entries() -> None:
    entries = [
        AllowlistEntry(
            package="requests", version="2.31.0",
            reason="reviewed", reviewed_by="alice",
            reviewed_at="2026-01-01T00:00:00Z",
        ),
        AllowlistEntry(
            package="flask", version="*",
            reason="trusted", reviewed_by="bob",
            reviewed_at="2026-02-01T00:00:00Z",
        ),
    ]
    with patch("sup.commands.allow.load_allowlist", return_value=entries):
        runner = CliRunner()
        result = runner.invoke(cli, ["allow", "list"])
        assert result.exit_code == 0
        assert "requests" in result.output
        assert "flask" in result.output
        assert "alice" in result.output


def test_allow_remove_success() -> None:
    with patch("sup.commands.allow.remove_from_allowlist", return_value=True):
        runner = CliRunner()
        result = runner.invoke(cli, ["allow", "remove", "requests", "2.31.0"])
        assert result.exit_code == 0
        assert "Removed" in result.output
