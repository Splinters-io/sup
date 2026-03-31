"""Package URL (purl) parser.

Purl spec: https://github.com/package-url/purl-spec

Examples:
    pkg:pypi/requests@2.31.0
    pkg:npm/express@4.18.2
    pkg:cargo/serde@1.0.197
    pkg:golang/github.com/gin-gonic/gin@v1.9.1
    pkg:gem/rails@7.1.2
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import unquote

from sup.models import Ecosystem

PURL_TYPE_TO_ECOSYSTEM: dict[str, Ecosystem] = {
    "pypi": Ecosystem.PYTHON,
    "npm": Ecosystem.NODE,
    "cargo": Ecosystem.RUST,
    "golang": Ecosystem.GO,
    "gem": Ecosystem.RUBY,
}


@dataclass(frozen=True)
class Purl:
    """Parsed package URL."""

    type: str
    namespace: str | None
    name: str
    version: str | None
    ecosystem: Ecosystem | None


def parse_purl(purl_str: str) -> Purl | None:
    """Parse a package URL string into its components.

    Returns None if the string is not a valid purl.
    """
    if not purl_str.startswith("pkg:"):
        return None

    # Strip scheme
    remainder = purl_str[4:]

    # Split off qualifiers and subpath (we don't need them)
    remainder = remainder.split("?")[0].split("#")[0]

    # Split type from the rest
    slash_idx = remainder.find("/")
    if slash_idx == -1:
        return None

    purl_type = remainder[:slash_idx]
    rest = unquote(remainder[slash_idx + 1:])

    # Extract version
    version: str | None = None
    at_idx = rest.rfind("@")
    if at_idx != -1:
        version = rest[at_idx + 1:]
        rest = rest[:at_idx]

    # For golang, the namespace is part of the name (e.g., github.com/gin-gonic/gin)
    # For others, split namespace/name
    if purl_type == "golang":
        namespace = None
        name = rest
    else:
        last_slash = rest.rfind("/")
        if last_slash != -1:
            namespace = rest[:last_slash]
            name = rest[last_slash + 1:]
        else:
            namespace = None
            name = rest

    ecosystem = PURL_TYPE_TO_ECOSYSTEM.get(purl_type)

    return Purl(
        type=purl_type,
        namespace=namespace,
        name=name,
        version=version,
        ecosystem=ecosystem,
    )
