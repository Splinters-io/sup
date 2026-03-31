"""Go module proxy registry client."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx

from sup.registries.base import MAX_RESPONSE_BYTES, validate_go_module, validate_version

DEFAULT_BASE_URL = "https://proxy.golang.org"


class GoClient:
    """Query publish dates from proxy.golang.org.

    Endpoint: GET /{module}/@v/{version}.info
    Date field: Time

    Note: The timestamp represents when the version was first cached by the proxy,
    not necessarily the original release time.
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL) -> None:
        self._base_url = base_url.rstrip("/")

    def get_publish_date(self, package: str, version: str) -> datetime | None:
        if not validate_go_module(package) or not validate_version(version):
            return None

        url = f"{self._base_url}/{package}/@v/{version}.info"
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

        time_str = data.get("Time")
        if not time_str or not isinstance(time_str, str):
            return None

        try:
            return datetime.fromisoformat(time_str.replace("Z", "+00:00")).astimezone(UTC)
        except (ValueError, AttributeError):
            return None
