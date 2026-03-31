"""Test lookup edge cases — cache miss writes to cache, NOT_FOUND from cache."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import respx

from sup.cache import set_cached_date
from sup.config import SupConfig
from sup.lookup import lookup_and_evaluate
from sup.models import Ecosystem, PackageInfo, RiskLevel, Tier


def _config() -> SupConfig:
    return SupConfig(
        known_days=10, bleeding_edge_days=14,
        default_tier=Tier.KNOWN, warn_only=False, registries={},
    )


@respx.mock
def test_lookup_cache_miss_writes_cache(tmp_path: Path) -> None:
    db = tmp_path / "cache.db"
    old = (datetime.now(UTC) - timedelta(days=100)).isoformat()
    route = respx.get("https://pypi.org/pypi/requests/json").mock(
        return_value=httpx.Response(200, json={"releases": {"2.31.0": [{"upload_time_iso_8601": old}]}})
    )

    allowlist = tmp_path / "empty_al.json"
    pkg = PackageInfo(name="requests", version="2.31.0", ecosystem=Ecosystem.PYTHON)
    result = lookup_and_evaluate(pkg, _config(), 10, 14, allowlist_path=allowlist, cache_db=db)
    assert result.risk_level == RiskLevel.SAFE
    assert route.call_count == 1

    # Second call should use cache
    result2 = lookup_and_evaluate(pkg, _config(), 10, 14, allowlist_path=allowlist, cache_db=db)
    assert result2.risk_level == RiskLevel.SAFE
    assert route.call_count == 1


def test_lookup_not_found_cached(tmp_path: Path) -> None:
    db = tmp_path / "cache.db"
    # Pre-populate cache with a NOT_FOUND entry
    set_cached_date("python", "missing", "1.0", None, db_path=db)

    pkg = PackageInfo(name="missing", version="1.0", ecosystem=Ecosystem.PYTHON)
    result = lookup_and_evaluate(pkg, _config(), 10, 14, cache_db=db)
    assert result.risk_level == RiskLevel.UNKNOWN
