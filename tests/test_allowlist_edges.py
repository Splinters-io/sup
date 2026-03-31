"""Test allowlist edge cases — non-list JSON, non-dict items."""

from pathlib import Path

from sup.allowlist import load_allowlist


def test_allowlist_non_list_json(tmp_path: Path) -> None:
    path = tmp_path / "allowlist.json"
    path.write_text('{"not": "a list"}')
    entries = load_allowlist(path)
    assert entries == []


def test_allowlist_non_dict_items(tmp_path: Path) -> None:
    path = tmp_path / "allowlist.json"
    path.write_text('["string", 42, null, {"package": "real", "version": "1.0"}]')
    entries = load_allowlist(path)
    assert len(entries) == 1
    assert entries[0].package == "real"
