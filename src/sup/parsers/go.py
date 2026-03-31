"""Parser for Go module files."""

from __future__ import annotations

import re
from pathlib import Path

# Matches: require github.com/foo/bar v1.2.3
_REQUIRE_SINGLE = re.compile(r"^\s*require\s+(\S+)\s+(v[\d.]+\S*)")
# Matches lines inside a require ( ... ) block
_REQUIRE_BLOCK_LINE = re.compile(r"^\s+(\S+)\s+(v[\d.]+\S*)")


class GoModParser:
    """Parse go.mod files."""

    def parse(self, path: Path) -> list[tuple[str, str]]:
        if path.name != "go.mod":
            return []

        content = path.read_text()
        results: list[tuple[str, str]] = []
        in_require_block = False

        for line in content.splitlines():
            stripped = line.strip()

            if stripped.startswith("require ("):
                in_require_block = True
                continue

            if in_require_block:
                if stripped == ")":
                    in_require_block = False
                    continue
                if stripped.startswith("//"):
                    continue
                match = _REQUIRE_BLOCK_LINE.match(line)
                if match:
                    results.append((match.group(1), match.group(2)))
                continue

            match = _REQUIRE_SINGLE.match(line)
            if match:
                results.append((match.group(1), match.group(2)))

        return results
