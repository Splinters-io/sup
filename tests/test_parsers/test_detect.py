"""Tests for ecosystem detection."""

from pathlib import Path

from sup.models import Ecosystem
from sup.parsers.detect import detect_ecosystem, find_dependency_files

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_detect_python(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("requests==2.31.0")
    result = detect_ecosystem(tmp_path)
    assert Ecosystem.PYTHON in result


def test_detect_node(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text('{"name": "test"}')
    result = detect_ecosystem(tmp_path)
    assert Ecosystem.NODE in result


def test_detect_go(tmp_path: Path) -> None:
    (tmp_path / "go.mod").write_text("module example.com/test")
    result = detect_ecosystem(tmp_path)
    assert Ecosystem.GO in result


def test_detect_rust(tmp_path: Path) -> None:
    (tmp_path / "Cargo.toml").write_text("[package]\nname = 'test'")
    result = detect_ecosystem(tmp_path)
    assert Ecosystem.RUST in result


def test_detect_ruby(tmp_path: Path) -> None:
    (tmp_path / "Gemfile.lock").write_text("GEM\n")
    result = detect_ecosystem(tmp_path)
    assert Ecosystem.RUBY in result


def test_detect_multiple(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("requests==1.0")
    (tmp_path / "package.json").write_text("{}")
    result = detect_ecosystem(tmp_path)
    assert Ecosystem.PYTHON in result
    assert Ecosystem.NODE in result


def test_detect_empty(tmp_path: Path) -> None:
    result = detect_ecosystem(tmp_path)
    assert result == []


def test_find_dependency_files() -> None:
    files = find_dependency_files(FIXTURES, Ecosystem.PYTHON)
    names = [f.name for f in files]
    assert "requirements.txt" in names
    assert "pyproject.toml" in names
