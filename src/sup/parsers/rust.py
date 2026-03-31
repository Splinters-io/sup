"""Parsers for Rust dependency files."""

from __future__ import annotations

import tomllib
from pathlib import Path


class RustParser:
    """Parse Cargo.toml and Cargo.lock files."""

    def parse(self, path: Path) -> list[tuple[str, str]]:
        if path.name == "Cargo.lock":
            return self._parse_cargo_lock(path)
        if path.name == "Cargo.toml":
            return self._parse_cargo_toml(path)
        return []

    def _parse_cargo_lock(self, path: Path) -> list[tuple[str, str]]:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        results: list[tuple[str, str]] = []
        for pkg in data.get("package", []):
            name = pkg.get("name", "")
            version = pkg.get("version", "")
            if name and version:
                results.append((name, version))
        return results

    def _parse_cargo_toml(self, path: Path) -> list[tuple[str, str]]:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        results: list[tuple[str, str]] = []
        for section in ("dependencies", "dev-dependencies", "build-dependencies"):
            deps = data.get(section, {})
            for name, value in deps.items():
                if isinstance(value, str):
                    results.append((name, value))
                elif isinstance(value, dict):
                    version = value.get("version", "")
                    if version:
                        results.append((name, version))
        return results
