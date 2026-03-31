"""Tests for Go module proxy registry client."""

from datetime import UTC, datetime

import httpx
import respx

from sup.registries.go import GoClient


@respx.mock
def test_get_publish_date_success() -> None:
    respx.get(
        "https://proxy.golang.org/github.com/gin-gonic/gin/@v/v1.9.1.info"
    ).mock(
        return_value=httpx.Response(
            200,
            json={"Version": "v1.9.1", "Time": "2023-06-15T10:30:45Z"},
        )
    )
    client = GoClient()
    result = client.get_publish_date("github.com/gin-gonic/gin", "v1.9.1")
    assert result == datetime(2023, 6, 15, 10, 30, 45, tzinfo=UTC)


@respx.mock
def test_version_not_found() -> None:
    respx.get(
        "https://proxy.golang.org/github.com/gin-gonic/gin/@v/v99.0.0.info"
    ).mock(return_value=httpx.Response(404))
    client = GoClient()
    assert client.get_publish_date("github.com/gin-gonic/gin", "v99.0.0") is None
