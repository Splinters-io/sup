"""Parse CycloneDX and SPDX SBOM formats."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path

from sup.models import Ecosystem, PackageInfo
from sup.sbom.purl import PURL_TYPE_TO_ECOSYSTEM, parse_purl


class SbomFormat(Enum):
    """Supported SBOM formats."""

    CYCLONEDX = "cyclonedx"
    SPDX = "spdx"


def detect_sbom_format(data: dict) -> SbomFormat | None:
    """Detect whether a parsed JSON dict is CycloneDX or SPDX."""
    if "bomFormat" in data and data["bomFormat"] == "CycloneDX":
        return SbomFormat.CYCLONEDX
    if "spdxVersion" in data:
        return SbomFormat.SPDX
    return None


def parse_sbom(path: Path) -> tuple[SbomFormat, list[PackageInfo], dict]:
    """Parse an SBOM file and return (format, packages, raw_data).

    The raw_data dict is returned for later enrichment/re-export.
    Raises ValueError if the format is unrecognised.
    """
    max_bytes = 50 * 1024 * 1024  # 50 MB
    if path.stat().st_size > max_bytes:
        raise ValueError(f"SBOM file exceeds {max_bytes // (1024 * 1024)} MB limit: {path}")

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"Invalid JSON in {path}: {e}") from e

    fmt = detect_sbom_format(raw)

    if fmt is None:
        raise ValueError(
            f"Unrecognised SBOM format in {path}. "
            "Expected CycloneDX or SPDX JSON."
        )

    if fmt == SbomFormat.CYCLONEDX:
        packages = _parse_cyclonedx(raw)
    else:
        packages = _parse_spdx(raw)

    return fmt, packages, raw


def _parse_cyclonedx(data: dict) -> list[PackageInfo]:
    """Extract packages from a CycloneDX SBOM.

    CycloneDX components have:
        - name (required)
        - version (optional)
        - purl (optional, best source for ecosystem)
        - type: "library", "framework", etc.
    """
    packages: list[PackageInfo] = []

    for component in data.get("components", []):
        name = component.get("name", "")
        version = component.get("version", "")
        purl_str = component.get("purl", "")

        if not name or not version:
            continue

        ecosystem = _resolve_ecosystem_cyclonedx(purl_str, component)
        if ecosystem is None:
            continue

        # For golang purls, the name includes the full module path
        purl = parse_purl(purl_str) if purl_str else None
        if purl and purl.ecosystem == Ecosystem.GO:
            name = purl.name

        packages.append(PackageInfo(name=name, version=version, ecosystem=ecosystem))

    return packages


def _resolve_ecosystem_cyclonedx(purl_str: str, component: dict) -> Ecosystem | None:
    """Resolve ecosystem from purl or component type hints."""
    if purl_str:
        purl = parse_purl(purl_str)
        if purl and purl.ecosystem:
            return purl.ecosystem

    # Fallback: check component properties for ecosystem hints
    for prop in component.get("properties", []):
        if prop.get("name") == "cdx:npm:package:type":
            return Ecosystem.NODE
    return None


def _parse_spdx(data: dict) -> list[PackageInfo]:
    """Extract packages from an SPDX SBOM.

    SPDX packages have:
        - name (required)
        - versionInfo (optional)
        - externalRefs[].referenceLocator (purl)
    """
    packages: list[PackageInfo] = []

    for pkg in data.get("packages", []):
        name = pkg.get("name", "")
        version = pkg.get("versionInfo", "")

        if not name or not version:
            continue

        ecosystem = _resolve_ecosystem_spdx(pkg)
        if ecosystem is None:
            continue

        # For golang, use the full module path from purl
        purl_str = _extract_purl_from_spdx(pkg)
        if purl_str:
            purl = parse_purl(purl_str)
            if purl and purl.ecosystem == Ecosystem.GO:
                name = purl.name

        packages.append(PackageInfo(name=name, version=version, ecosystem=ecosystem))

    return packages


def _resolve_ecosystem_spdx(pkg: dict) -> Ecosystem | None:
    """Resolve ecosystem from SPDX external references."""
    purl_str = _extract_purl_from_spdx(pkg)
    if purl_str:
        purl = parse_purl(purl_str)
        if purl and purl.ecosystem:
            return purl.ecosystem
    return None


def _extract_purl_from_spdx(pkg: dict) -> str | None:
    """Extract purl string from SPDX externalRefs."""
    for ref in pkg.get("externalRefs", []):
        if ref.get("referenceType") == "purl":
            return ref.get("referenceLocator", "")
    return None
