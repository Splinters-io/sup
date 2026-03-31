"""Tests for PyPI registry client."""

from datetime import UTC, datetime

import httpx
import respx

from sup.registries.pypi import PyPIClient


@respx.mock
def test_get_publish_date_success() -> None:
    respx.get("https://pypi.org/pypi/requests/json").mock(
        return_value=httpx.Response(
            200,
            json={
                "releases": {
                    "2.31.0": [
                        {
                            "filename": "requests-2.31.0.tar.gz",
                            "upload_time_iso_8601": "2023-05-22T15:12:44.175Z",
                        }
                    ]
                }
            },
        )
    )
    client = PyPIClient()
    result = client.get_publish_date("requests", "2.31.0")
    assert result == datetime(2023, 5, 22, 15, 12, 44, 175000, tzinfo=UTC)


@respx.mock
def test_get_publish_date_version_not_found() -> None:
    respx.get("https://pypi.org/pypi/requests/json").mock(
        return_value=httpx.Response(200, json={"releases": {}})
    )
    client = PyPIClient()
    assert client.get_publish_date("requests", "99.99.99") is None


@respx.mock
def test_get_publish_date_package_not_found() -> None:
    respx.get("https://pypi.org/pypi/nonexistent/json").mock(
        return_value=httpx.Response(404)
    )
    client = PyPIClient()
    assert client.get_publish_date("nonexistent", "1.0.0") is None


@respx.mock
def test_custom_base_url() -> None:
    respx.get("https://private.pypi.org/pypi/mypkg/json").mock(
        return_value=httpx.Response(
            200,
            json={
                "releases": {
                    "1.0.0": [
                        {"upload_time_iso_8601": "2024-01-01T00:00:00Z"}
                    ]
                }
            },
        )
    )
    client = PyPIClient(base_url="https://private.pypi.org")
    result = client.get_publish_date("mypkg", "1.0.0")
    assert result is not None
