"""Tests for the cached, allowlist-aware lookup module."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import respx

from sup.allowlist import add_to_allowlist
from sup.config import SupConfig
from sup.lookup import lookup_and_evaluate
from sup.models import Ecosystem, PackageInfo, RiskLevel, Tier


def _make_config() -> SupConfig:
    return SupConfig(
        known_days=10,
        bleeding_edge_days=14,
        default_tier=Tier.KNOWN,
        warn_only=False,
        registries={},
    )


@respx.mock
def test_lookup_caches_result(tmp_path: Path) -> None:
    db = tmp_path / "cache.db"
    old_date = (datetime.now(UTC) - timedelta(days=100)).isoformat()
    route = respx.get("https://pypi.org/pypi/requests/json").mock(
        return_value=httpx.Response(
            200,
            json={"releases": {"2.31.0": [{"upload_time_iso_8601": old_date}]}},
        )
    )

    pkg = PackageInfo(name="requests", version="2.31.0", ecosystem=Ecosystem.PYTHON)
    config = _make_config()

    allowlist = tmp_path / "empty_allowlist.json"

    # First call — hits registry
    result1 = lookup_and_evaluate(pkg, config, 10, 14, allowlist_path=allowlist, cache_db=db)
    assert result1.risk_level == RiskLevel.SAFE
    assert route.call_count == 1

    # Second call — from cache, no registry hit
    result2 = lookup_and_evaluate(pkg, config, 10, 14, allowlist_path=allowlist, cache_db=db)
    assert result2.risk_level == RiskLevel.SAFE
    assert route.call_count == 1  # Still 1


def test_lookup_allowlist_bypasses_registry(tmp_path: Path) -> None:
    allowlist = tmp_path / "allowlist.json"
    db = tmp_path / "cache.db"
    add_to_allowlist("newpkg", "1.0.0", "reviewed it", "me", allowlist)

    pkg = PackageInfo(name="newpkg", version="1.0.0", ecosystem=Ecosystem.PYTHON)
    config = _make_config()

    # No registry mock needed — allowlist should short-circuit
    result = lookup_and_evaluate(
        pkg, config, 10, 14, allowlist_path=allowlist, cache_db=db,
    )
    assert result.is_safe is True
    assert result.risk_level == RiskLevel.SAFE
