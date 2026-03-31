"""Tests for Node.js dependency parsers."""

from pathlib import Path

from sup.parsers.node import NodeParser

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_parse_package_json() -> None:
    parser = NodeParser()
    result = parser.parse(FIXTURES / "package.json")
    assert ("express", "4.18.0") in result
    assert ("lodash", "4.17.21") in result
    assert ("jest", "29.7.0") in result
    assert len(result) == 3


def test_parse_package_lock_json() -> None:
    parser = NodeParser()
    result = parser.parse(FIXTURES / "package-lock.json")
    assert ("express", "4.18.2") in result
    assert ("lodash", "4.17.21") in result
    assert len(result) == 2


def test_parse_yarn_lock() -> None:
    parser = NodeParser()
    result = parser.parse(FIXTURES / "yarn.lock")
    assert ("express", "4.18.2") in result
    assert ("lodash", "4.17.21") in result
    assert len(result) == 2
