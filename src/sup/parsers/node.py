"""Parsers for Node.js dependency files."""

from __future__ import annotations

import json
import re
from pathlib import Path

# yarn.lock: "package@^1.0.0": followed by version "1.0.5"
_YARN_VERSION = re.compile(r'^\s+version\s+"([^"]+)"')
_YARN_HEADER = re.compile(r'^"?(@?[^@\s"]+)@')


class NodeParser:
    """Parse Node.js dependency files."""

    def parse(self, path: Path) -> list[tuple[str, str]]:
        name = path.name
        if name == "package-lock.json":
            return self._parse_package_lock(path)
        if name == "package.json":
            return self._parse_package_json(path)
        if name == "yarn.lock":
            return self._parse_yarn_lock(path)
        return []

    def _parse_package_json(self, path: Path) -> list[tuple[str, str]]:
        data = json.loads(path.read_text())
        results: list[tuple[str, str]] = []
        for section in ("dependencies", "devDependencies"):
            deps = data.get(section, {})
            for name, version in deps.items():
                # Strip range operators for display
                clean = version.lstrip("^~>=<")
                if clean:
                    results.append((name, clean))
        return results

    def _parse_package_lock(self, path: Path) -> list[tuple[str, str]]:
        data = json.loads(path.read_text())
        results: list[tuple[str, str]] = []

        # v2/v3 format: packages dict
        packages = data.get("packages", {})
        for pkg_path, info in packages.items():
            if not pkg_path:  # Skip root entry
                continue
            # Extract package name from path like "node_modules/express"
            name = pkg_path.split("node_modules/")[-1]
            version = info.get("version", "")
            if name and version:
                results.append((name, version))

        return results

    def _parse_yarn_lock(self, path: Path) -> list[tuple[str, str]]:
        results: list[tuple[str, str]] = []
        current_name: str | None = None

        for line in path.read_text().splitlines():
            if not line or line.startswith("#"):
                continue

            header_match = _YARN_HEADER.match(line)
            if header_match and not line.startswith(" "):
                current_name = header_match.group(1)
                continue

            if current_name:
                version_match = _YARN_VERSION.match(line)
                if version_match:
                    results.append((current_name, version_match.group(1)))
                    current_name = None

        return results
