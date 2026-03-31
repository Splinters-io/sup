"""Tests for sup config command."""

from pathlib import Path

from click.testing import CliRunner

from sup.cli import cli


def test_config_init(tmp_path: Path) -> None:
    """sup config --init should create a config file."""
    from unittest.mock import patch

    config_path = tmp_path / "config.toml"
    with patch("sup.commands.config_cmd.init_config", return_value=config_path) as mock:
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "--init"])
        assert result.exit_code == 0
        assert "Config created" in result.output


def test_config_show() -> None:
    """sup config --show should display current settings."""
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "--show"])
    assert result.exit_code == 0
    assert "Known tier" in result.output
    assert "10 days" in result.output


def test_config_no_args() -> None:
    """sup config with no args should show help."""
    runner = CliRunner()
    result = runner.invoke(cli, ["config"])
    assert result.exit_code == 0
    assert "--init" in result.output
