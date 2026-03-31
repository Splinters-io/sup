"""Tests for parser edge cases — unknown file types."""

from pathlib import Path

from sup.parsers.go import GoModParser
from sup.parsers.node import NodeParser
from sup.parsers.python import PythonParser
from sup.parsers.ruby import RubyParser


def test_python_unknown_file(tmp_path: Path) -> None:
    p = tmp_path / "unknown.xyz"
    p.write_text("")
    assert PythonParser().parse(p) == []


def test_node_unknown_file(tmp_path: Path) -> None:
    p = tmp_path / "unknown.xyz"
    p.write_text("")
    assert NodeParser().parse(p) == []


def test_go_non_gomod(tmp_path: Path) -> None:
    p = tmp_path / "go.sum"
    p.write_text("")
    assert GoModParser().parse(p) == []


def test_ruby_non_gemlock(tmp_path: Path) -> None:
    p = tmp_path / "Gemfile"
    p.write_text("")
    assert RubyParser().parse(p) == []
