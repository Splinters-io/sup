"""crates.io registry client."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx

from sup.registries.base import MAX_RESPONSE_BYTES, validate_crates_name, validate_version

DEFAULT_BASE_URL = "https://crates.io"


class CratesClient:
    """Query publish dates from the crates.io API.

    Endpoint: GET /api/v1/crates/{crate}/versions
    Date field: versions[].created_at
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL) -> None:
        self._base_url = base_url.rstrip("/")

    def get_publish_date(self, package: str, version: str) -> datetime | None:
        if not validate_crates_name(package) or not validate_version(version):
            return None

        url = f"{self._base_url}/api/v1/crates/{package}/versions"
        headers = {"User-Agent": "sup-quarantine/0.1.0"}
        try:
            response = httpx.get(url, headers=headers, timeout=30)
        except httpx.HTTPError:
            return None

        if response.status_code != 200:
            return None
        if len(response.content) > MAX_RESPONSE_BYTES:
            return None

        try:
            data = response.json()
        except ValueError:
            return None

        for ver_info in data.get("versions", []):
            if not isinstance(ver_info, dict):
                continue
            if ver_info.get("num") == version:
                created = ver_info.get("created_at")
                if created and isinstance(created, str):
                    try:
                        return datetime.fromisoformat(
                            created.replace("Z", "+00:00")
                        ).astimezone(UTC)
                    except (ValueError, AttributeError):
                        return None
        return None
