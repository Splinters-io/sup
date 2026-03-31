"""Test response size limits for all registry clients."""

import httpx
import respx

from sup.registries.crates import CratesClient
from sup.registries.go import GoClient
from sup.registries.npm import NpmClient
from sup.registries.pypi import PyPIClient
from sup.registries.rubygems import RubyGemsClient

BIG = b"x" * (11 * 1024 * 1024)


@respx.mock
def test_npm_response_too_large() -> None:
    respx.get("https://registry.npmjs.org/express").mock(
        return_value=httpx.Response(200, content=BIG)
    )
    assert NpmClient().get_publish_date("express", "1.0") is None


@respx.mock
def test_crates_response_too_large() -> None:
    respx.get("https://crates.io/api/v1/crates/serde/versions").mock(
        return_value=httpx.Response(200, content=BIG)
    )
    assert CratesClient().get_publish_date("serde", "1.0") is None


@respx.mock
def test_go_response_too_large() -> None:
    url = "https://proxy.golang.org/github.com/gin-gonic/gin/@v/v1.0.info"
    respx.get(url).mock(return_value=httpx.Response(200, content=BIG))
    assert GoClient().get_publish_date("github.com/gin-gonic/gin", "v1.0") is None


@respx.mock
def test_rubygems_response_too_large() -> None:
    respx.get("https://rubygems.org/api/v1/versions/rails.json").mock(
        return_value=httpx.Response(200, content=BIG)
    )
    assert RubyGemsClient().get_publish_date("rails", "1.0") is None


@respx.mock
def test_pypi_upload_time_missing() -> None:
    """First file has no upload_time_iso_8601 field."""
    respx.get("https://pypi.org/pypi/pkg/json").mock(
        return_value=httpx.Response(200, json={"releases": {"1.0": [{"filename": "pkg.tar.gz"}]}})
    )
    assert PyPIClient().get_publish_date("pkg", "1.0") is None
