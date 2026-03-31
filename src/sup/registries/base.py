"""Base protocol and safety utilities for registry clients."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Protocol

# Maximum response body size (10 MB) to prevent memory exhaustion
MAX_RESPONSE_BYTES = 10 * 1024 * 1024

# Ecosystem-specific package name patterns
_PYPI_NAME = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$")
_NPM_NAME = re.compile(r"^(@[a-zA-Z0-9._-]+/)?[a-zA-Z0-9._-]+$")
_CRATES_NAME = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]*$")
_GO_MODULE = re.compile(r"^[a-zA-Z0-9._~:/?#\[\]@!$&'()*+,;=-]+(/[a-zA-Z0-9._~:/?#\[\]@!$&'()*+,;=-]+)*$")
_GEM_NAME = re.compile(r"^[a-zA-Z0-9._-]+$")
_VERSION_SAFE = re.compile(r"^[a-zA-Z0-9._+~-]+$")


class RegistryClient(Protocol):
    """Protocol that all registry clients must implement."""

    def get_publish_date(self, package: str, version: str) -> datetime | None:
        """Return the publish date for a specific package version, or None if unknown."""
        ...


def validate_pypi_name(name: str) -> bool:
    return bool(_PYPI_NAME.match(name))


def validate_npm_name(name: str) -> bool:
    return bool(_NPM_NAME.match(name))


def validate_crates_name(name: str) -> bool:
    return bool(_CRATES_NAME.match(name))


def validate_go_module(name: str) -> bool:
    """Go modules contain slashes (e.g., github.com/foo/bar) but no .."""
    return bool(_GO_MODULE.match(name)) and ".." not in name


def validate_gem_name(name: str) -> bool:
    return bool(_GEM_NAME.match(name))


def validate_version(version: str) -> bool:
    """Version strings must not contain path separators or control chars."""
    return bool(_VERSION_SAFE.match(version))
