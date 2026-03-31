"""Test purl edge case: pkg:type with no slash after type."""

from sup.sbom.purl import parse_purl


def test_purl_no_slash_after_type() -> None:
    result = parse_purl("pkg:pypi")
    assert result is None
