"""Auto-detect project ecosystem by file presence."""

from __future__ import annotations

from pathlib import Path

from sup.models import Ecosystem

# Files that indicate each ecosystem, in priority order
ECOSYSTEM_FILES: dict[Ecosystem, list[str]] = {
    Ecosystem.PYTHON: [
        "poetry.lock",
        "Pipfile.lock",
        "requirements.txt",
        "pyproject.toml",
    ],
    Ecosystem.NODE: [
        "package-lock.json",
        "yarn.lock",
        "package.json",
    ],
    Ecosystem.GO: ["go.mod"],
    Ecosystem.RUST: ["Cargo.lock", "Cargo.toml"],
    Ecosystem.RUBY: ["Gemfile.lock", "Gemfile"],
}


def detect_ecosystem(project_dir: Path) -> list[Ecosystem]:
    """Detect which ecosystems are present in the project directory."""
    found: list[Ecosystem] = []
    for ecosystem, files in ECOSYSTEM_FILES.items():
        if any((project_dir / f).exists() for f in files):
            found.append(ecosystem)
    return found


def find_dependency_files(project_dir: Path, ecosystem: Ecosystem) -> list[Path]:
    """Find dependency files for a specific ecosystem in the project directory."""
    files = ECOSYSTEM_FILES.get(ecosystem, [])
    return [project_dir / f for f in files if (project_dir / f).exists()]
