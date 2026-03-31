"""Tests for sup config command edge cases."""

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from sup.cli import cli


def test_config_init_direct(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    with patch("sup.commands.config_cmd.init_config", return_value=path):
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "--init"])
        assert result.exit_code == 0
        assert "Config created" in result.output


def test_config_show_with_registries(tmp_path: Path) -> None:
    from sup.config import SupConfig
    from sup.models import Tier

    cfg = SupConfig(
        known_days=10, bleeding_edge_days=14,
        default_tier=Tier.KNOWN, warn_only=False,
        registries={"pypi": "https://private.pypi.org"},
    )
    with patch("sup.commands.config_cmd.load_config", return_value=cfg):
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "--show"])
        assert result.exit_code == 0
        assert "private.pypi.org" in result.output
