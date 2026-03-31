"""npm registry client."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx

from sup.registries.base import MAX_RESPONSE_BYTES, validate_npm_name, validate_version

DEFAULT_BASE_URL = "https://registry.npmjs.org"


class NpmClient:
    """Query publish dates from the npm registry.

    Endpoint: GET /{package}
    Date field: time[version]

    Note: The `time` field was dropped from npm metadata responses in March 2021.
    It may be absent for some packages. When missing, this client returns None.
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL) -> None:
        self._base_url = base_url.rstrip("/")

    def get_publish_date(self, package: str, version: str) -> datetime | None:
        if not validate_npm_name(package) or not validate_version(version):
            return None

        url = f"{self._base_url}/{package}"
        try:
            response = httpx.get(url, timeout=30)
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

        time_map = data.get("time", {})
        if not isinstance(time_map, dict):
            return None

        timestamp = time_map.get(version)
        if not timestamp or not isinstance(timestamp, str):
            return None

        try:
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).astimezone(UTC)
        except (ValueError, AttributeError):
            return None
