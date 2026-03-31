"""Configuration loading and management for sup."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import tomli_w

from sup.models import TIER_DEFAULTS, Tier

CONFIG_DIR = Path.home() / ".config" / "sup"
CONFIG_PATH = CONFIG_DIR / "config.toml"

# Maximum config file size (1 MB)
MAX_CONFIG_BYTES = 1 * 1024 * 1024

DEFAULT_CONFIG: dict[str, object] = {
    "tiers": {
        "known": TIER_DEFAULTS[Tier.KNOWN],
        "bleeding_edge": TIER_DEFAULTS[Tier.BLEEDING_EDGE],
    },
    "behavior": {
        "default_tier": "known",
        "warn_only": False,
    },
    "registries": {},
}


@dataclass(frozen=True)
class SupConfig:
    """Loaded sup configuration."""

    known_days: int
    bleeding_edge_days: int
    default_tier: Tier
    warn_only: bool
    registries: dict[str, str]


def load_config(path: Path | None = None) -> SupConfig:
    """Load configuration from TOML file, falling back to defaults."""
    config_path = path or CONFIG_PATH
    raw: dict = dict(DEFAULT_CONFIG)

    if config_path.exists():
        if config_path.stat().st_size > MAX_CONFIG_BYTES:
            raise ValueError(f"Config file exceeds {MAX_CONFIG_BYTES} bytes: {config_path}")

        try:
            with open(config_path, "rb") as f:
                user_config = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise ValueError(f"Invalid TOML in {config_path}: {e}") from e

        raw = _merge(raw, user_config)

    tiers = raw.get("tiers", {})
    behavior = raw.get("behavior", {})

    # Validate tier
    tier_str = behavior.get("default_tier", "known")
    try:
        default_tier = Tier(tier_str)
    except ValueError:
        raise ValueError(
            f"Invalid default_tier '{tier_str}' in config. "
            f"Must be 'known' or 'bleeding_edge'."
        )

    # Validate day thresholds
    known_days = tiers.get("known", TIER_DEFAULTS[Tier.KNOWN])
    bleeding_edge_days = tiers.get("bleeding_edge", TIER_DEFAULTS[Tier.BLEEDING_EDGE])
    if not isinstance(known_days, int) or known_days < 0:
        raise ValueError(f"tiers.known must be a non-negative integer, got: {known_days!r}")
    if not isinstance(bleeding_edge_days, int) or bleeding_edge_days < 0:
        raise ValueError(
            f"tiers.bleeding_edge must be a non-negative integer, got: {bleeding_edge_days!r}"
        )

    # Validate registry URLs
    registries = raw.get("registries", {})
    if isinstance(registries, dict):
        for name, url in registries.items():
            _validate_registry_url(name, url)
    else:
        registries = {}

    return SupConfig(
        known_days=known_days,
        bleeding_edge_days=bleeding_edge_days,
        default_tier=default_tier,
        warn_only=bool(behavior.get("warn_only", False)),
        registries=registries,
    )


def init_config(path: Path | None = None) -> Path:
    """Create a default config file. Returns the path written."""
    config_path = path or CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "wb") as f:
        tomli_w.dump(DEFAULT_CONFIG, f)
    return config_path


def _merge(base: dict, override: dict, depth: int = 0) -> dict:
    """Deep-merge override into base, returning a new dict."""
    if depth > 10:
        raise ValueError("Config nesting too deep (max 10 levels)")
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge(result[key], value, depth + 1)
        else:
            result[key] = value
    return result


def _validate_registry_url(name: str, url: str) -> None:
    """Validate that a custom registry URL is safe."""
    if not isinstance(url, str):
        raise ValueError(f"Registry URL for '{name}' must be a string")

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(
            f"Registry '{name}' has unsupported scheme '{parsed.scheme}'. "
            f"Only http:// and https:// are allowed."
        )

    hostname = parsed.hostname or ""
    # Block cloud metadata endpoints and loopback
    blocked = {"169.254.169.254", "metadata.google.internal", "localhost", "127.0.0.1", "::1"}
    if hostname in blocked:
        raise ValueError(
            f"Registry '{name}' points to a blocked address: {hostname}"
        )
