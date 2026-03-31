"""Tests for Rust dependency parsers."""

from pathlib import Path

from sup.parsers.rust import RustParser

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_parse_cargo_lock() -> None:
    parser = RustParser()
    result = parser.parse(FIXTURES / "Cargo.lock")
    assert ("serde", "1.0.200") in result
    assert ("tokio", "1.37.0") in result
    assert len(result) == 2


def test_parse_cargo_toml_string_deps() -> None:
    parser = RustParser()
    result = parser.parse(FIXTURES / "Cargo.toml")
    assert ("serde", "1.0.200") in result


def test_parse_cargo_toml_table_deps() -> None:
    parser = RustParser()
    result = parser.parse(FIXTURES / "Cargo.toml")
    assert ("tokio", "1.37.0") in result


def test_parse_cargo_toml_dev_and_build_deps() -> None:
    parser = RustParser()
    result = parser.parse(FIXTURES / "Cargo.toml")
    assert ("criterion", "0.5.1") in result
    assert ("cc", "1.0.90") in result
    assert len(result) == 4


def test_parse_unknown_file() -> None:
    parser = RustParser()
    result = parser.parse(FIXTURES / "requirements.txt")
    assert result == []
