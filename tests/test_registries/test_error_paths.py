"""Tests for registry client error handling — covers all safety branches."""

import httpx
import respx

from sup.registries.crates import CratesClient
from sup.registries.go import GoClient
from sup.registries.npm import NpmClient
from sup.registries.pypi import PyPIClient
from sup.registries.rubygems import RubyGemsClient


# --- Input validation ---


def test_pypi_invalid_name() -> None:
    assert PyPIClient().get_publish_date("../evil", "1.0") is None


def test_pypi_invalid_version() -> None:
    assert PyPIClient().get_publish_date("requests", "../bad") is None


def test_npm_invalid_name() -> None:
    assert NpmClient().get_publish_date("../../etc/passwd", "1.0") is None


def test_npm_invalid_version() -> None:
    assert NpmClient().get_publish_date("express", "1.0/../../") is None


def test_crates_invalid_name() -> None:
    assert CratesClient().get_publish_date("../evil", "1.0") is None


def test_go_invalid_module() -> None:
    assert GoClient().get_publish_date("../../../evil", "v1.0") is None


def test_go_dotdot_in_module() -> None:
    assert GoClient().get_publish_date("github.com/../evil", "v1.0") is None


def test_gem_invalid_name() -> None:
    assert RubyGemsClient().get_publish_date("../evil", "1.0") is None


# --- Network errors ---


@respx.mock
def test_pypi_network_error() -> None:
    respx.get("https://pypi.org/pypi/requests/json").mock(side_effect=httpx.ConnectError("fail"))
    assert PyPIClient().get_publish_date("requests", "1.0") is None


@respx.mock
def test_npm_network_error() -> None:
    respx.get("https://registry.npmjs.org/express").mock(side_effect=httpx.TimeoutException("slow"))
    assert NpmClient().get_publish_date("express", "1.0") is None


@respx.mock
def test_crates_network_error() -> None:
    respx.get("https://crates.io/api/v1/crates/serde/versions").mock(side_effect=httpx.ConnectError("fail"))
    assert CratesClient().get_publish_date("serde", "1.0") is None


@respx.mock
def test_go_network_error() -> None:
    url = "https://proxy.golang.org/github.com/gin-gonic/gin/@v/v1.0.info"
    respx.get(url).mock(side_effect=httpx.ReadTimeout("slow"))
    assert GoClient().get_publish_date("github.com/gin-gonic/gin", "v1.0") is None


@respx.mock
def test_rubygems_network_error() -> None:
    respx.get("https://rubygems.org/api/v1/versions/rails.json").mock(side_effect=httpx.ConnectError("fail"))
    assert RubyGemsClient().get_publish_date("rails", "1.0") is None


# --- Bad JSON ---


@respx.mock
def test_pypi_bad_json() -> None:
    respx.get("https://pypi.org/pypi/requests/json").mock(
        return_value=httpx.Response(200, content=b"<html>not json</html>")
    )
    assert PyPIClient().get_publish_date("requests", "1.0") is None


@respx.mock
def test_npm_bad_json() -> None:
    respx.get("https://registry.npmjs.org/express").mock(
        return_value=httpx.Response(200, content=b"not json")
    )
    assert NpmClient().get_publish_date("express", "1.0") is None


@respx.mock
def test_crates_bad_json() -> None:
    respx.get("https://crates.io/api/v1/crates/serde/versions").mock(
        return_value=httpx.Response(200, content=b"nope")
    )
    assert CratesClient().get_publish_date("serde", "1.0") is None


@respx.mock
def test_go_bad_json() -> None:
    url = "https://proxy.golang.org/github.com/gin-gonic/gin/@v/v1.0.info"
    respx.get(url).mock(return_value=httpx.Response(200, content=b"nope"))
    assert GoClient().get_publish_date("github.com/gin-gonic/gin", "v1.0") is None


@respx.mock
def test_rubygems_bad_json() -> None:
    respx.get("https://rubygems.org/api/v1/versions/rails.json").mock(
        return_value=httpx.Response(200, content=b"nope")
    )
    assert RubyGemsClient().get_publish_date("rails", "1.0") is None


# --- Malformed response data ---


@respx.mock
def test_pypi_version_files_not_list() -> None:
    respx.get("https://pypi.org/pypi/pkg/json").mock(
        return_value=httpx.Response(200, json={"releases": {"1.0": "not-a-list"}})
    )
    assert PyPIClient().get_publish_date("pkg", "1.0") is None


@respx.mock
def test_pypi_first_file_not_dict() -> None:
    respx.get("https://pypi.org/pypi/pkg/json").mock(
        return_value=httpx.Response(200, json={"releases": {"1.0": ["not-a-dict"]}})
    )
    assert PyPIClient().get_publish_date("pkg", "1.0") is None


@respx.mock
def test_pypi_bad_timestamp() -> None:
    respx.get("https://pypi.org/pypi/pkg/json").mock(
        return_value=httpx.Response(200, json={"releases": {"1.0": [{"upload_time_iso_8601": "not-a-date"}]}})
    )
    assert PyPIClient().get_publish_date("pkg", "1.0") is None


@respx.mock
def test_npm_time_not_dict() -> None:
    respx.get("https://registry.npmjs.org/express").mock(
        return_value=httpx.Response(200, json={"time": "not-a-dict"})
    )
    assert NpmClient().get_publish_date("express", "1.0") is None


@respx.mock
def test_npm_timestamp_not_string() -> None:
    respx.get("https://registry.npmjs.org/express").mock(
        return_value=httpx.Response(200, json={"time": {"1.0": 12345}})
    )
    assert NpmClient().get_publish_date("express", "1.0") is None


@respx.mock
def test_npm_bad_timestamp() -> None:
    respx.get("https://registry.npmjs.org/express").mock(
        return_value=httpx.Response(200, json={"time": {"1.0": "not-a-date"}})
    )
    assert NpmClient().get_publish_date("express", "1.0") is None


@respx.mock
def test_crates_version_info_not_dict() -> None:
    respx.get("https://crates.io/api/v1/crates/serde/versions").mock(
        return_value=httpx.Response(200, json={"versions": ["not-a-dict"]})
    )
    assert CratesClient().get_publish_date("serde", "1.0") is None


@respx.mock
def test_crates_bad_timestamp() -> None:
    respx.get("https://crates.io/api/v1/crates/serde/versions").mock(
        return_value=httpx.Response(200, json={"versions": [{"num": "1.0", "created_at": "bad"}]})
    )
    assert CratesClient().get_publish_date("serde", "1.0") is None


@respx.mock
def test_go_time_not_string() -> None:
    url = "https://proxy.golang.org/github.com/gin-gonic/gin/@v/v1.0.info"
    respx.get(url).mock(return_value=httpx.Response(200, json={"Time": 12345}))
    assert GoClient().get_publish_date("github.com/gin-gonic/gin", "v1.0") is None


@respx.mock
def test_go_bad_timestamp() -> None:
    url = "https://proxy.golang.org/github.com/gin-gonic/gin/@v/v1.0.info"
    respx.get(url).mock(return_value=httpx.Response(200, json={"Time": "not-a-date"}))
    assert GoClient().get_publish_date("github.com/gin-gonic/gin", "v1.0") is None


@respx.mock
def test_rubygems_not_list() -> None:
    respx.get("https://rubygems.org/api/v1/versions/rails.json").mock(
        return_value=httpx.Response(200, json={"not": "a list"})
    )
    assert RubyGemsClient().get_publish_date("rails", "1.0") is None


@respx.mock
def test_rubygems_version_not_dict() -> None:
    respx.get("https://rubygems.org/api/v1/versions/rails.json").mock(
        return_value=httpx.Response(200, json=["not-a-dict"])
    )
    assert RubyGemsClient().get_publish_date("rails", "1.0") is None


@respx.mock
def test_rubygems_bad_timestamp() -> None:
    respx.get("https://rubygems.org/api/v1/versions/rails.json").mock(
        return_value=httpx.Response(200, json=[{"number": "1.0", "created_at": "bad"}])
    )
    assert RubyGemsClient().get_publish_date("rails", "1.0") is None


# --- Response too large ---


@respx.mock
def test_pypi_response_too_large() -> None:
    respx.get("https://pypi.org/pypi/requests/json").mock(
        return_value=httpx.Response(200, content=b"x" * (11 * 1024 * 1024))
    )
    assert PyPIClient().get_publish_date("requests", "1.0") is None
