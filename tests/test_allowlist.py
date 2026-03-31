"""Tests for the allowlist."""

from pathlib import Path

from sup.allowlist import (
    add_to_allowlist,
    is_allowed,
    load_allowlist,
    remove_from_allowlist,
    save_allowlist,
)


def test_empty_allowlist(tmp_path: Path) -> None:
    path = tmp_path / "allowlist.json"
    entries = load_allowlist(path)
    assert entries == []


def test_add_and_load(tmp_path: Path) -> None:
    path = tmp_path / "allowlist.json"
    add_to_allowlist("requests", "2.31.0", "reviewed", "alice", path)
    entries = load_allowlist(path)
    assert len(entries) == 1
    assert entries[0].package == "requests"
    assert entries[0].version == "2.31.0"
    assert entries[0].reason == "reviewed"
    assert entries[0].reviewed_by == "alice"


def test_is_allowed_exact_version(tmp_path: Path) -> None:
    path = tmp_path / "allowlist.json"
    add_to_allowlist("requests", "2.31.0", "reviewed", "alice", path)
    assert is_allowed("requests", "2.31.0", path) is not None
    assert is_allowed("requests", "2.32.0", path) is None


def test_is_allowed_wildcard(tmp_path: Path) -> None:
    path = tmp_path / "allowlist.json"
    add_to_allowlist("requests", "*", "all versions ok", "alice", path)
    assert is_allowed("requests", "2.31.0", path) is not None
    assert is_allowed("requests", "99.0.0", path) is not None
    assert is_allowed("flask", "1.0.0", path) is None


def test_remove(tmp_path: Path) -> None:
    path = tmp_path / "allowlist.json"
    add_to_allowlist("requests", "2.31.0", "ok", "alice", path)
    assert remove_from_allowlist("requests", "2.31.0", path) is True
    assert is_allowed("requests", "2.31.0", path) is None


def test_remove_nonexistent(tmp_path: Path) -> None:
    path = tmp_path / "allowlist.json"
    assert remove_from_allowlist("nope", "1.0", path) is False


def test_upsert(tmp_path: Path) -> None:
    path = tmp_path / "allowlist.json"
    add_to_allowlist("requests", "2.31.0", "first review", "alice", path)
    add_to_allowlist("requests", "2.31.0", "second review", "bob", path)
    entries = load_allowlist(path)
    assert len(entries) == 1
    assert entries[0].reviewed_by == "bob"


def test_corrupt_file(tmp_path: Path) -> None:
    path = tmp_path / "allowlist.json"
    path.write_text("not json at all")
    entries = load_allowlist(path)
    assert entries == []
