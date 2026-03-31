"""RubyGems registry client."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx

from sup.registries.base import MAX_RESPONSE_BYTES, validate_gem_name, validate_version

DEFAULT_BASE_URL = "https://rubygems.org"


class RubyGemsClient:
    """Query publish dates from the RubyGems API.

    Endpoint: GET /api/v1/versions/{gem}.json
    Date field: [].created_at
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL) -> None:
        self._base_url = base_url.rstrip("/")

    def get_publish_date(self, package: str, version: str) -> datetime | None:
        if not validate_gem_name(package) or not validate_version(version):
            return None

        url = f"{self._base_url}/api/v1/versions/{package}.json"
        try:
            response = httpx.get(url, timeout=30)
        except httpx.HTTPError:
            return None

        if response.status_code != 200:
            return None
        if len(response.content) > MAX_RESPONSE_BYTES:
            return None

        try:
            versions = response.json()
        except ValueError:
            return None

        if not isinstance(versions, list):
            return None

        for ver_info in versions:
            if not isinstance(ver_info, dict):
                continue
            if ver_info.get("number") == version:
                created = ver_info.get("created_at")
                if created and isinstance(created, str):
                    try:
                        return datetime.fromisoformat(
                            created.replace("Z", "+00:00")
                        ).astimezone(UTC)
                    except (ValueError, AttributeError):
                        return None
        return None
