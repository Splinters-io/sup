"""Enrich SBOMs with quarantine status annotations."""

from __future__ import annotations

import copy
import json
from datetime import UTC, datetime
from pathlib import Path

from sup import __version__
from sup.models import QuarantineResult
from sup.sbom.parse import SbomFormat


def enrich_sbom(
    raw_data: dict,
    fmt: SbomFormat,
    results: list[QuarantineResult],
    tier_name: str,
    required_days: int,
) -> dict:
    """Return a new SBOM dict enriched with quarantine annotations.

    Does not mutate raw_data.
    """
    enriched = copy.deepcopy(raw_data)

    if fmt == SbomFormat.CYCLONEDX:
        return _enrich_cyclonedx(enriched, results, tier_name, required_days)
    return _enrich_spdx(enriched, results, tier_name, required_days)


def write_enriched_sbom(data: dict, output_path: Path) -> None:
    """Write an enriched SBOM dict to a JSON file."""
    output_path.write_text(json.dumps(data, indent=2, default=str) + "\n")


def _enrich_cyclonedx(
    data: dict,
    results: list[QuarantineResult],
    tier_name: str,
    required_days: int,
) -> dict:
    """Add quarantine properties to CycloneDX components.

    Uses the CycloneDX properties extension point:
    https://cyclonedx.org/docs/1.5/json/#components_items_properties
    """
    result_map = _build_result_map(results)

    for component in data.get("components", []):
        name = component.get("name", "")
        version = component.get("version", "")
        key = f"{name}@{version}"

        result = result_map.get(key)
        if result is None:
            continue

        props = component.setdefault("properties", [])
        props.extend(_quarantine_properties(result, tier_name, required_days))

    # Add tool metadata
    metadata = data.setdefault("metadata", {})
    tools = metadata.setdefault("tools", [])
    tools.append({
        "vendor": "sup",
        "name": "sup-quarantine",
        "version": __version__,
    })

    return data


def _enrich_spdx(
    data: dict,
    results: list[QuarantineResult],
    tier_name: str,
    required_days: int,
) -> dict:
    """Add quarantine annotations to SPDX packages.

    Uses SPDX annotations:
    https://spdx.github.io/spdx-spec/v2.3/annotations/
    """
    result_map = _build_result_map(results)
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    annotations = data.setdefault("annotations", [])

    for pkg in data.get("packages", []):
        name = pkg.get("name", "")
        version = pkg.get("versionInfo", "")
        spdx_id = pkg.get("SPDXID", "")
        key = f"{name}@{version}"

        result = result_map.get(key)
        if result is None:
            continue

        status = result.risk_level.value
        age_str = f"{result.age_days}d" if result.age_days is not None else "unknown"
        publish_str = (
            result.publish_date.strftime("%Y-%m-%d")
            if result.publish_date
            else "unknown"
        )

        annotation_text = (
            f"sup-quarantine: status={status}, "
            f"age={age_str}, "
            f"published={publish_str}, "
            f"tier={tier_name}, "
            f"threshold={required_days}d"
        )

        annotations.append({
            "annotationDate": now,
            "annotationType": "REVIEW",
            "annotator": f"Tool: sup-quarantine-{__version__}",
            "comment": annotation_text,
            **({"SPDXID": spdx_id} if spdx_id else {}),
        })

    # Add creator tool
    creation_info = data.get("creationInfo", {})
    creators = creation_info.get("creators", [])
    creators.append(f"Tool: sup-quarantine-{__version__}")
    creation_info["creators"] = creators
    data["creationInfo"] = creation_info

    return data


def _build_result_map(results: list[QuarantineResult]) -> dict[str, QuarantineResult]:
    """Build a lookup map from 'name@version' to QuarantineResult."""
    return {
        f"{r.package.name}@{r.package.version}": r
        for r in results
    }


def _quarantine_properties(
    result: QuarantineResult,
    tier_name: str,
    required_days: int,
) -> list[dict[str, str]]:
    """Generate CycloneDX property entries for a quarantine result."""
    status = result.risk_level.value
    props = [
        {"name": "sup:quarantine:status", "value": status},
        {"name": "sup:quarantine:tier", "value": tier_name},
        {"name": "sup:quarantine:threshold_days", "value": str(required_days)},
    ]

    if result.age_days is not None:
        props.append({"name": "sup:quarantine:age_days", "value": str(result.age_days)})

    if result.publish_date:
        props.append({
            "name": "sup:quarantine:publish_date",
            "value": result.publish_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        })

    if result.error:
        props.append({"name": "sup:quarantine:error", "value": result.error})

    return props
