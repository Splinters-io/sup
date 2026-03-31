"""Tests for RubyGems registry client."""

from datetime import UTC, datetime

import httpx
import respx

from sup.registries.rubygems import RubyGemsClient


@respx.mock
def test_get_publish_date_success() -> None:
    respx.get("https://rubygems.org/api/v1/versions/rails.json").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"number": "7.1.0", "created_at": "2023-10-05T00:00:00Z"},
                {"number": "7.0.8", "created_at": "2023-09-09T00:00:00Z"},
            ],
        )
    )
    client = RubyGemsClient()
    result = client.get_publish_date("rails", "7.0.8")
    assert result == datetime(2023, 9, 9, 0, 0, 0, tzinfo=UTC)


@respx.mock
def test_version_not_found() -> None:
    respx.get("https://rubygems.org/api/v1/versions/rails.json").mock(
        return_value=httpx.Response(200, json=[{"number": "7.1.0", "created_at": "2023-10-05T00:00:00Z"}])
    )
    client = RubyGemsClient()
    assert client.get_publish_date("rails", "99.0.0") is None


@respx.mock
def test_package_not_found() -> None:
    respx.get("https://rubygems.org/api/v1/versions/nonexistent.json").mock(
        return_value=httpx.Response(404)
    )
    client = RubyGemsClient()
    assert client.get_publish_date("nonexistent", "1.0.0") is None
