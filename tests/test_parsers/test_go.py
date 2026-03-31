"""Tests for Go module parser."""

from pathlib import Path

from sup.parsers.go import GoModParser

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_parse_go_mod() -> None:
    parser = GoModParser()
    result = parser.parse(FIXTURES / "go.mod")
    assert ("github.com/gin-gonic/gin", "v1.9.1") in result
    assert ("github.com/stretchr/testify", "v1.8.4") in result
    assert ("golang.org/x/text", "v0.14.0") in result
    assert ("github.com/modern-go/concurrent", "v0.0.0-20180228061459-e0a39a4cb421") in result
    assert len(result) == 4
