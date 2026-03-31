"""Tests for the local registry cache."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from sup.cache import cache_stats, clear_cache, get_cached_date, set_cached_date


def test_cache_miss(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    result = get_cached_date("python", "requests", "2.31.0", db_path=db)
    assert result is None


def test_cache_hit(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    now = datetime.now(UTC)
    set_cached_date("python", "requests", "2.31.0", now, db_path=db)
    result = get_cached_date("python", "requests", "2.31.0", db_path=db)
    assert isinstance(result, datetime)


def test_cache_not_found(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    set_cached_date("python", "missing", "1.0.0", None, db_path=db)
    result = get_cached_date("python", "missing", "1.0.0", db_path=db)
    assert result == "NOT_FOUND"


def test_cache_expiry(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    set_cached_date("python", "old", "1.0.0", datetime.now(UTC), db_path=db)
    # With a TTL of 0 hours, everything is expired
    result = get_cached_date("python", "old", "1.0.0", ttl_hours=0, db_path=db)
    assert result is None


def test_clear_cache(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    set_cached_date("python", "a", "1.0", datetime.now(UTC), db_path=db)
    set_cached_date("python", "b", "1.0", datetime.now(UTC), db_path=db)
    count = clear_cache(db_path=db)
    assert count == 2
    assert get_cached_date("python", "a", "1.0", db_path=db) is None


def test_cache_stats(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    set_cached_date("python", "a", "1.0", datetime.now(UTC), db_path=db)
    set_cached_date("python", "b", "2.0", datetime.now(UTC), db_path=db)
    stats = cache_stats(db_path=db)
    assert stats["total"] == 2
    assert stats["fresh"] == 2
    assert stats["expired"] == 0


def test_cache_upsert(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    date1 = datetime(2024, 1, 1, tzinfo=UTC)
    date2 = datetime(2024, 6, 1, tzinfo=UTC)
    set_cached_date("python", "pkg", "1.0", date1, db_path=db)
    set_cached_date("python", "pkg", "1.0", date2, db_path=db)
    result = get_cached_date("python", "pkg", "1.0", db_path=db)
    assert isinstance(result, datetime)
    assert result.month == 6
