"""Tests for crates.io registry client."""

from datetime import UTC, datetime

import httpx
import respx

from sup.registries.crates import CratesClient


@respx.mock
def test_get_publish_date_success() -> None:
    respx.get("https://crates.io/api/v1/crates/serde/versions").mock(
        return_value=httpx.Response(
            200,
            json={
                "versions": [
                    {"num": "1.0.200", "created_at": "2024-06-01T12:00:00Z"},
                    {"num": "1.0.199", "created_at": "2024-05-15T10:30:00Z"},
                ]
            },
        )
    )
    client = CratesClient()
    result = client.get_publish_date("serde", "1.0.199")
    assert result == datetime(2024, 5, 15, 10, 30, 0, tzinfo=UTC)


@respx.mock
def test_version_not_found() -> None:
    respx.get("https://crates.io/api/v1/crates/serde/versions").mock(
        return_value=httpx.Response(200, json={"versions": []})
    )
    client = CratesClient()
    assert client.get_publish_date("serde", "99.0.0") is None


@respx.mock
def test_package_not_found() -> None:
    respx.get("https://crates.io/api/v1/crates/nonexistent/versions").mock(
        return_value=httpx.Response(404)
    )
    client = CratesClient()
    assert client.get_publish_date("nonexistent", "1.0.0") is None
