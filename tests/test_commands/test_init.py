"""Tests for sup init command."""

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from sup.cli import cli


def test_init_all(tmp_path: Path, monkeypatch: object) -> None:
    import os
    # Use monkeypatch from pytest
    monkeypatch.setattr(os, "getcwd", lambda: str(tmp_path))  # type: ignore[attr-defined]
    monkeypatch.chdir(tmp_path)  # type: ignore[attr-defined]

    with patch("sup.commands.init.init_config", return_value=tmp_path / "config.toml"):
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--all"])
        assert result.exit_code == 0
        assert "Config created" in result.output
        assert "pre-commit-config" in result.output
        assert "Quick start" in result.output
        assert (tmp_path / ".github" / "workflows" / "sup-quarantine.yml").exists()


def test_init_default_is_all(tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.chdir(tmp_path)  # type: ignore[attr-defined]

    with patch("sup.commands.init.init_config", return_value=tmp_path / "config.toml"):
        runner = CliRunner()
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0
        assert "Config created" in result.output


def test_init_github_action_only(tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.chdir(tmp_path)  # type: ignore[attr-defined]
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "--github-action"])
    assert result.exit_code == 0
    assert (tmp_path / ".github" / "workflows" / "sup-quarantine.yml").exists()


def test_init_github_action_already_exists(tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.chdir(tmp_path)  # type: ignore[attr-defined]
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "sup-quarantine.yml").write_text("existing")
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "--github-action"])
    assert "Already exists" in result.output


def test_init_pre_commit_only(tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.chdir(tmp_path)  # type: ignore[attr-defined]
    runner = CliRunner()
    result = runner.invoke(cli, ["init", "--pre-commit"])
    assert "pre-commit-config" in result.output


def test_init_config_only(tmp_path: Path) -> None:
    with patch("sup.commands.init.init_config", return_value=Path("/tmp/config.toml")):
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--config"])
        assert result.exit_code == 0
        assert "Config created" in result.output
