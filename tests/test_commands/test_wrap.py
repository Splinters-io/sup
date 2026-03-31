"""Tests for sup wrap command."""

from sup.commands.wrap import _extract_packages, _parse_package_spec
from sup.models import Ecosystem, PackageInfo


def test_parse_pip_spec() -> None:
    result = _parse_package_spec("requests==2.31.0", Ecosystem.PYTHON)
    assert result == PackageInfo(name="requests", version="2.31.0", ecosystem=Ecosystem.PYTHON)


def test_parse_pip_no_version() -> None:
    result = _parse_package_spec("requests", Ecosystem.PYTHON)
    assert result is None


def test_parse_npm_spec() -> None:
    result = _parse_package_spec("express@4.18.2", Ecosystem.NODE)
    assert result == PackageInfo(name="express", version="4.18.2", ecosystem=Ecosystem.NODE)


def test_parse_npm_scoped() -> None:
    result = _parse_package_spec("@angular/core@16.0.0", Ecosystem.NODE)
    assert result == PackageInfo(name="@angular/core", version="16.0.0", ecosystem=Ecosystem.NODE)


def test_parse_cargo_spec() -> None:
    result = _parse_package_spec("serde@1.0.197", Ecosystem.RUST)
    assert result == PackageInfo(name="serde", version="1.0.197", ecosystem=Ecosystem.RUST)


def test_parse_go_spec() -> None:
    result = _parse_package_spec("github.com/gin-gonic/gin@v1.9.1", Ecosystem.GO)
    assert result is not None
    assert result.name == "github.com/gin-gonic/gin"
    assert result.version == "v1.9.1"


def test_extract_pip_install() -> None:
    cmd = ("pip", "install", "requests==2.31.0", "flask==3.0.0")
    packages = _extract_packages(cmd, Ecosystem.PYTHON)
    assert len(packages) == 2
    assert packages[0].name == "requests"
    assert packages[1].name == "flask"


def test_extract_skips_flags() -> None:
    cmd = ("pip", "install", "--upgrade", "requests==2.31.0", "-r", "requirements.txt")
    packages = _extract_packages(cmd, Ecosystem.PYTHON)
    assert len(packages) == 1
    assert packages[0].name == "requests"


def test_extract_npm_install() -> None:
    cmd = ("npm", "install", "express@4.18.2")
    packages = _extract_packages(cmd, Ecosystem.NODE)
    assert len(packages) == 1
    assert packages[0].name == "express"


def test_extract_no_specs() -> None:
    cmd = ("pip", "install", "-r", "requirements.txt")
    packages = _extract_packages(cmd, Ecosystem.PYTHON)
    assert packages == []
