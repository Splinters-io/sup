"""Allowlist for packages that have been manually reviewed."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

ALLOWLIST_PATH = Path.home() / ".config" / "sup" / "allowlist.json"


@dataclass(frozen=True)
class AllowlistEntry:
    """A reviewed package that bypasses quarantine."""

    package: str
    version: str
    reason: str
    reviewed_by: str
    reviewed_at: str


def load_allowlist(path: Path | None = None) -> list[AllowlistEntry]:
    """Load the allowlist from disk."""
    allowlist_path = path or ALLOWLIST_PATH
    if not allowlist_path.exists():
        return []

    try:
        data = json.loads(allowlist_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return []

    if not isinstance(data, list):
        return []

    entries: list[AllowlistEntry] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        entries.append(
            AllowlistEntry(
                package=item.get("package", ""),
                version=item.get("version", "*"),
                reason=item.get("reason", ""),
                reviewed_by=item.get("reviewed_by", ""),
                reviewed_at=item.get("reviewed_at", ""),
            )
        )
    return entries


def save_allowlist(entries: list[AllowlistEntry], path: Path | None = None) -> Path:
    """Save the allowlist to disk."""
    allowlist_path = path or ALLOWLIST_PATH
    allowlist_path.parent.mkdir(parents=True, exist_ok=True)
    data = [
        {
            "package": e.package,
            "version": e.version,
            "reason": e.reason,
            "reviewed_by": e.reviewed_by,
            "reviewed_at": e.reviewed_at,
        }
        for e in entries
    ]
    allowlist_path.write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8"
    )
    return allowlist_path


def add_to_allowlist(
    package: str,
    version: str,
    reason: str,
    reviewed_by: str,
    path: Path | None = None,
) -> AllowlistEntry:
    """Add a package to the allowlist."""
    entries = load_allowlist(path)
    entry = AllowlistEntry(
        package=package,
        version=version,
        reason=reason,
        reviewed_by=reviewed_by,
        reviewed_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    # Replace existing entry for same package+version
    filtered = [e for e in entries if not (e.package == package and e.version == version)]
    filtered.append(entry)
    save_allowlist(filtered, path)
    return entry


def is_allowed(package: str, version: str, path: Path | None = None) -> AllowlistEntry | None:
    """Check if a package+version is on the allowlist.

    Returns the matching entry, or None if not allowed.
    Supports wildcard version ("*") to allow all versions of a package.
    """
    entries = load_allowlist(path)
    for entry in entries:
        if entry.package == package and entry.version in (version, "*"):
            return entry
    return None


def remove_from_allowlist(
    package: str, version: str, path: Path | None = None,
) -> bool:
    """Remove a package from the allowlist. Returns True if found and removed."""
    entries = load_allowlist(path)
    filtered = [e for e in entries if not (e.package == package and e.version in (version, "*"))]
    if len(filtered) == len(entries):
        return False
    save_allowlist(filtered, path)
    return True
