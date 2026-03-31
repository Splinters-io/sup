"""Parser for Ruby Gemfile.lock files."""

from __future__ import annotations

import re
from pathlib import Path

# Matches: "    gemname (1.2.3)" inside GEM specs section
_GEM_SPEC = re.compile(r"^\s{4}(\S+)\s+\(([^)]+)\)")


class RubyParser:
    """Parse Gemfile.lock files."""

    def parse(self, path: Path) -> list[tuple[str, str]]:
        if path.name != "Gemfile.lock":
            return []

        content = path.read_text()
        results: list[tuple[str, str]] = []
        in_specs = False

        for line in content.splitlines():
            stripped = line.strip()

            if stripped == "specs:":
                in_specs = True
                continue

            if in_specs:
                if not line.startswith("  "):
                    in_specs = False
                    continue
                match = _GEM_SPEC.match(line)
                if match:
                    results.append((match.group(1), match.group(2)))

        return results
