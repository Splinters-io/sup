"""PyPI registry client."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx

from sup.registries.base import MAX_RESPONSE_BYTES, validate_pypi_name, validate_version

DEFAULT_BASE_URL = "https://pypi.org"


class PyPIClient:
    """Query publish dates from the PyPI JSON API.

    Endpoint: GET /pypi/{package}/json
    Date field: releases[version][0].upload_time_iso_8601
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL) -> None:
        self._base_url = base_url.rstrip("/")

    def get_publish_date(self, package: str, version: str) -> datetime | None:
        if not validate_pypi_name(package) or not validate_version(version):
            return None

        url = f"{self._base_url}/pypi/{package}/json"
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

        releases = data.get("releases", {})
        version_files = releases.get(version, [])

        if not version_files or not isinstance(version_files, list):
            return None

        first_file = version_files[0]
        if not isinstance(first_file, dict):
            return None

        upload_time = first_file.get("upload_time_iso_8601")
        if not upload_time:
            return None

        try:
            return datetime.fromisoformat(upload_time.replace("Z", "+00:00")).astimezone(UTC)
        except (ValueError, AttributeError):
            return None
