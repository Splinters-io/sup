"""Local SQLite cache for registry publish dates."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "sup"
CACHE_DB = CACHE_DIR / "registry.db"
DEFAULT_TTL_HOURS = 24


def _get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or CACHE_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute(
        """CREATE TABLE IF NOT EXISTS publish_dates (
            ecosystem TEXT NOT NULL,
            package TEXT NOT NULL,
            version TEXT NOT NULL,
            publish_date TEXT,
            cached_at TEXT NOT NULL,
            PRIMARY KEY (ecosystem, package, version)
        )"""
    )
    return conn


def get_cached_date(
    ecosystem: str,
    package: str,
    version: str,
    ttl_hours: int = DEFAULT_TTL_HOURS,
    db_path: Path | None = None,
) -> datetime | None | str:
    """Look up a cached publish date.

    Returns:
        datetime — cached publish date (cache hit)
        None — cache miss (not in cache or expired)
        "NOT_FOUND" — we previously looked this up and got no result
    """
    conn = _get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT publish_date, cached_at FROM publish_dates "
            "WHERE ecosystem = ? AND package = ? AND version = ?",
            (ecosystem, package, version),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    publish_date_str, cached_at_str = row
    cached_at = datetime.fromisoformat(cached_at_str)

    if datetime.now(UTC) - cached_at > timedelta(hours=ttl_hours):
        return None  # expired

    if publish_date_str is None:
        return "NOT_FOUND"

    return datetime.fromisoformat(publish_date_str)


def set_cached_date(
    ecosystem: str,
    package: str,
    version: str,
    publish_date: datetime | None,
    db_path: Path | None = None,
) -> None:
    """Store a publish date in the cache."""
    conn = _get_connection(db_path)
    now = datetime.now(UTC).isoformat()
    date_str = publish_date.isoformat() if publish_date else None
    try:
        conn.execute(
            "INSERT OR REPLACE INTO publish_dates "
            "(ecosystem, package, version, publish_date, cached_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (ecosystem, package, version, date_str, now),
        )
        conn.commit()
    finally:
        conn.close()


def clear_cache(db_path: Path | None = None) -> int:
    """Clear all cached entries. Returns number of rows deleted."""
    conn = _get_connection(db_path)
    try:
        cursor = conn.execute("DELETE FROM publish_dates")
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def cache_stats(db_path: Path | None = None) -> dict[str, int]:
    """Return cache statistics."""
    conn = _get_connection(db_path)
    try:
        total = conn.execute("SELECT COUNT(*) FROM publish_dates").fetchone()[0]
        expired_cutoff = (
            datetime.now(UTC) - timedelta(hours=DEFAULT_TTL_HOURS)
        ).isoformat()
        fresh = conn.execute(
            "SELECT COUNT(*) FROM publish_dates WHERE cached_at > ?",
            (expired_cutoff,),
        ).fetchone()[0]
        return {"total": total, "fresh": fresh, "expired": total - fresh}
    finally:
        conn.close()
