"""Tests for config loading, validation, and error paths."""

from pathlib import Path

import pytest

from sup.config import _merge, _validate_registry_url, init_config, load_config


def test_load_defaults(tmp_path: Path) -> None:
    config = load_config(tmp_path / "nonexistent.toml")
    assert config.known_days == 10
    assert config.bleeding_edge_days == 14


def test_load_valid_config(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('[tiers]\nknown = 7\nbleeding_edge = 21\n')
    config = load_config(p)
    assert config.known_days == 7
    assert config.bleeding_edge_days == 21


def test_load_config_too_large(tmp_path: Path) -> None:
    p = tmp_path / "big.toml"
    p.write_text("x = " + "'" + "a" * (2 * 1024 * 1024) + "'")
    with pytest.raises(ValueError, match="exceeds"):
        load_config(p)


def test_load_config_invalid_toml(tmp_path: Path) -> None:
    p = tmp_path / "bad.toml"
    p.write_text("this is not valid toml [[[")
    with pytest.raises(ValueError, match="Invalid TOML"):
        load_config(p)


def test_load_config_invalid_tier(tmp_path: Path) -> None:
    p = tmp_path / "bad_tier.toml"
    p.write_text('[behavior]\ndefault_tier = "yolo"\n')
    with pytest.raises(ValueError, match="Invalid default_tier"):
        load_config(p)


def test_load_config_negative_days(tmp_path: Path) -> None:
    p = tmp_path / "neg.toml"
    p.write_text("[tiers]\nknown = -5\n")
    with pytest.raises(ValueError, match="non-negative integer"):
        load_config(p)


def test_load_config_string_days(tmp_path: Path) -> None:
    p = tmp_path / "str.toml"
    p.write_text('[tiers]\nbleeding_edge = "ten"\n')
    with pytest.raises(ValueError, match="non-negative integer"):
        load_config(p)


def test_load_config_registries_not_dict(tmp_path: Path) -> None:
    p = tmp_path / "reglist.toml"
    p.write_text('registries = ["not", "a", "dict"]\n')
    config = load_config(p)
    assert config.registries == {}


def test_load_config_valid_registry(tmp_path: Path) -> None:
    p = tmp_path / "reg.toml"
    p.write_text('[registries]\npypi = "https://private.pypi.org"\n')
    config = load_config(p)
    assert config.registries["pypi"] == "https://private.pypi.org"


def test_init_config(tmp_path: Path) -> None:
    path = init_config(tmp_path / "new.toml")
    assert path.exists()
    config = load_config(path)
    assert config.known_days == 10


def test_validate_registry_url_bad_scheme() -> None:
    with pytest.raises(ValueError, match="unsupported scheme"):
        _validate_registry_url("test", "ftp://evil.com")


def test_validate_registry_url_blocked_host() -> None:
    with pytest.raises(ValueError, match="blocked address"):
        _validate_registry_url("test", "http://169.254.169.254")


def test_validate_registry_url_localhost() -> None:
    with pytest.raises(ValueError, match="blocked address"):
        _validate_registry_url("test", "http://localhost/pypi")


def test_validate_registry_url_not_string() -> None:
    with pytest.raises(ValueError, match="must be a string"):
        _validate_registry_url("test", 12345)  # type: ignore[arg-type]


def test_merge_depth_limit() -> None:
    # Build base and override both nested 12 levels deep so merge recurses past 10
    base: dict = {}
    override: dict = {}
    b_cur = base
    o_cur = override
    for _ in range(12):
        b_cur["a"] = {}
        o_cur["a"] = {}
        b_cur = b_cur["a"]
        o_cur = o_cur["a"]
    o_cur["val"] = 1
    with pytest.raises(ValueError, match="too deep"):
        _merge(base, override)
