"""Cached, allowlist-aware package lookup.

This module is the single entry point for commands that need to evaluate
packages. It handles: cache → registry → cache write → allowlist check.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sup.allowlist import is_allowed
from sup.cache import get_cached_date, set_cached_date
from sup.config import SupConfig
from sup.models import PackageInfo, QuarantineResult, RiskLevel
from sup.quarantine import evaluate
from sup.registries import get_client


def lookup_and_evaluate(
    pkg: PackageInfo,
    config: SupConfig,
    required_days: int,
    bleeding_edge_days: int,
    allowlist_path: Path | None = None,
    cache_db: Path | None = None,
) -> QuarantineResult:
    """Look up a package's publish date (cached) and evaluate quarantine status.

    If the package is on the allowlist, it's marked safe regardless of age.
    """
    # 1. Check allowlist first
    entry = is_allowed(pkg.name, pkg.version, allowlist_path)
    if entry is not None:
        return QuarantineResult(
            package=pkg,
            publish_date=None,
            age_days=None,
            required_days=required_days,
            is_safe=True,
            risk_level=RiskLevel.SAFE,
            error=None,
        )

    # 2. Check cache
    publish_date = _get_publish_date_cached(pkg, config, cache_db)

    # 3. Evaluate
    return evaluate(pkg, publish_date, required_days, bleeding_edge_days)


def _get_publish_date_cached(
    pkg: PackageInfo,
    config: SupConfig,
    cache_db: Path | None,
) -> datetime | None:
    """Get publish date, using cache when available."""
    eco = pkg.ecosystem.value

    cached = get_cached_date(eco, pkg.name, pkg.version, db_path=cache_db)
    if isinstance(cached, datetime):
        return cached
    if cached == "NOT_FOUND":
        return None

    # Cache miss — query registry
    client = get_client(pkg.ecosystem, base_url=config.registries.get(eco))
    publish_date = client.get_publish_date(pkg.name, pkg.version)

    # Store result (even None, so we don't re-query)
    set_cached_date(eco, pkg.name, pkg.version, publish_date, db_path=cache_db)

    return publish_date
