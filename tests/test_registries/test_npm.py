"""Tests for npm registry client."""

from datetime import UTC, datetime

import httpx
import respx

from sup.registries.npm import NpmClient


@respx.mock
def test_get_publish_date_success() -> None:
    respx.get("https://registry.npmjs.org/express").mock(
        return_value=httpx.Response(
            200,
            json={
                "time": {
                    "4.18.0": "2022-04-25T17:22:45.756Z",
                    "created": "2010-12-29T19:38:25.450Z",
                }
            },
        )
    )
    client = NpmClient()
    result = client.get_publish_date("express", "4.18.0")
    assert result == datetime(2022, 4, 25, 17, 22, 45, 756000, tzinfo=UTC)


@respx.mock
def test_get_publish_date_time_field_missing() -> None:
    """npm dropped the time field in March 2021 — handle gracefully."""
    respx.get("https://registry.npmjs.org/express").mock(
        return_value=httpx.Response(200, json={"name": "express"})
    )
    client = NpmClient()
    assert client.get_publish_date("express", "4.18.0") is None


@respx.mock
def test_get_publish_date_version_not_in_time() -> None:
    respx.get("https://registry.npmjs.org/express").mock(
        return_value=httpx.Response(200, json={"time": {"1.0.0": "2010-01-01T00:00:00Z"}})
    )
    client = NpmClient()
    assert client.get_publish_date("express", "99.0.0") is None


@respx.mock
def test_package_not_found() -> None:
    respx.get("https://registry.npmjs.org/nonexistent-pkg-xyz").mock(
        return_value=httpx.Response(404)
    )
    client = NpmClient()
    assert client.get_publish_date("nonexistent-pkg-xyz", "1.0.0") is None
