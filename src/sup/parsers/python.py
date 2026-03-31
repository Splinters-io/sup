"""Parsers for Python dependency files."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

# Matches: package==version or package[extras]==version
_REQ_PATTERN = re.compile(r"^([a-zA-Z0-9_][a-zA-Z0-9._-]*)(?:\[.*?\])?\s*==\s*([^\s;#]+)")

# Matches PEP 621 dependency specs: "package>=1.0,<2" — extracts pinned version if ==
_PEP621_PINNED = re.compile(r"^([a-zA-Z0-9_][a-zA-Z0-9._-]*)(?:\[.*?\])?\s*==\s*([^\s,;]+)")

# Matches version ranges like ">=1.0,<2.0" — extracts the lower bound
_PEP621_LOWER = re.compile(r"^([a-zA-Z0-9_][a-zA-Z0-9._-]*)(?:\[.*?\])?\s*>=\s*([^\s,;]+)")


class PythonParser:
    """Parse Python dependency files."""

    def parse(self, path: Path) -> list[tuple[str, str]]:
        name = path.name
        if name == "requirements.txt":
            return self._parse_requirements(path)
        if name == "pyproject.toml":
            return self._parse_pyproject(path)
        if name == "poetry.lock":
            return self._parse_poetry_lock(path)
        if name == "Pipfile.lock":
            return self._parse_pipfile_lock(path)
        return []

    def _parse_requirements(self, path: Path) -> list[tuple[str, str]]:
        results: list[tuple[str, str]] = []
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            match = _REQ_PATTERN.match(line)
            if match:
                results.append((match.group(1), match.group(2)))
        return results

    def _parse_pyproject(self, path: Path) -> list[tuple[str, str]]:
        with open(path, "rb") as f:
            data = tomllib.load(f)

        deps = data.get("project", {}).get("dependencies", [])
        results: list[tuple[str, str]] = []
        for dep in deps:
            match = _PEP621_PINNED.match(dep)
            if match:
                results.append((match.group(1), match.group(2)))
                continue
            match = _PEP621_LOWER.match(dep)
            if match:
                results.append((match.group(1), match.group(2)))
        return results

    def _parse_poetry_lock(self, path: Path) -> list[tuple[str, str]]:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        results: list[tuple[str, str]] = []
        for pkg in data.get("package", []):
            name = pkg.get("name", "")
            version = pkg.get("version", "")
            if name and version:
                results.append((name, version))
        return results

    def _parse_pipfile_lock(self, path: Path) -> list[tuple[str, str]]:
        data = json.loads(path.read_text())
        results: list[tuple[str, str]] = []
        for section in ("default", "develop"):
            packages = data.get(section, {})
            for name, info in packages.items():
                version = info.get("version", "")
                if version.startswith("=="):
                    version = version[2:]
                if name and version:
                    results.append((name, version))
        return results
