"""Tests for Ruby Gemfile.lock parser."""

from pathlib import Path

from sup.parsers.ruby import RubyParser

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_parse_gemfile_lock() -> None:
    parser = RubyParser()
    result = parser.parse(FIXTURES / "Gemfile.lock")
    assert ("actioncable", "7.1.0") in result
    assert ("actionmailer", "7.1.0") in result
    assert ("rails", "7.1.0") in result
    assert len(result) == 3
