"""Tests for sup allow CLI commands."""

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from sup.cli import cli


def test_allow_add(tmp_path: Path) -> None:
    path = tmp_path / "allowlist.json"
    with patch("sup.commands.allow.add_to_allowlist", wraps=None) as mock:
        from sup.allowlist import AllowlistEntry

        mock.return_value = AllowlistEntry(
            package="requests", version="2.31.0",
            reason="reviewed", reviewed_by="alice",
            reviewed_at="2026-01-01T00:00:00Z",
        )
        runner = CliRunner()
        result = runner.invoke(
            cli, ["allow", "add", "requests", "2.31.0", "-r", "reviewed", "--by", "alice"]
        )
        assert result.exit_code == 0
        assert "Allowed" in result.output


def test_allow_list_empty() -> None:
    with patch("sup.commands.allow.load_allowlist", return_value=[]):
        runner = CliRunner()
        result = runner.invoke(cli, ["allow", "list"])
        assert result.exit_code == 0
        assert "empty" in result.output


def test_allow_remove_not_found() -> None:
    with patch("sup.commands.allow.remove_from_allowlist", return_value=False):
        runner = CliRunner()
        result = runner.invoke(cli, ["allow", "remove", "nope", "1.0"])
        assert result.exit_code == 0
        assert "Not found" in result.output
