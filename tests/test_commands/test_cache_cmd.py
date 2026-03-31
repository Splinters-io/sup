"""Tests for sup cache CLI commands."""

from unittest.mock import patch

from click.testing import CliRunner

from sup.cli import cli


def test_cache_clear() -> None:
    with patch("sup.commands.cache_cmd.clear_cache", return_value=5):
        runner = CliRunner()
        result = runner.invoke(cli, ["cache", "clear"])
        assert result.exit_code == 0
        assert "Cleared 5" in result.output


def test_cache_stats() -> None:
    with patch("sup.commands.cache_cmd.cache_stats", return_value={"total": 10, "fresh": 8, "expired": 2}):
        runner = CliRunner()
        result = runner.invoke(cli, ["cache", "stats"])
        assert result.exit_code == 0
        assert "10" in result.output
        assert "8" in result.output
        assert "2" in result.output
