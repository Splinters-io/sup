"""Base protocol and dispatcher for dependency parsers."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from sup.models import Ecosystem


class DependencyParser(Protocol):
    """Protocol for dependency file parsers."""

    def parse(self, path: Path) -> list[tuple[str, str]]:
        """Parse a dependency file and return list of (name, version) tuples."""
        ...


def parse_dependencies(project_dir: Path, ecosystem: Ecosystem) -> list[tuple[str, str]]:
    """Parse dependencies for the given ecosystem from the project directory."""
    from sup.parsers.detect import find_dependency_files
    from sup.parsers.go import GoModParser
    from sup.parsers.node import NodeParser
    from sup.parsers.python import PythonParser
    from sup.parsers.ruby import RubyParser
    from sup.parsers.rust import RustParser

    parser_map: dict[Ecosystem, DependencyParser] = {
        Ecosystem.PYTHON: PythonParser(),
        Ecosystem.NODE: NodeParser(),
        Ecosystem.GO: GoModParser(),
        Ecosystem.RUST: RustParser(),
        Ecosystem.RUBY: RubyParser(),
    }

    parser = parser_map[ecosystem]
    files = find_dependency_files(project_dir, ecosystem)

    results: list[tuple[str, str]] = []
    for file_path in files:
        results.extend(parser.parse(file_path))

    # Deduplicate, keeping first occurrence
    seen: set[str] = set()
    unique: list[tuple[str, str]] = []
    for name, version in results:
        if name not in seen:
            seen.add(name)
            unique.append((name, version))
    return unique
