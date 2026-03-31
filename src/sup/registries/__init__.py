"""Package registry clients for querying publish dates."""

from sup.registries.base import RegistryClient
from sup.registries.crates import CratesClient
from sup.registries.go import GoClient
from sup.registries.npm import NpmClient
from sup.registries.pypi import PyPIClient
from sup.registries.rubygems import RubyGemsClient
from sup.models import Ecosystem

REGISTRY_MAP: dict[Ecosystem, type[RegistryClient]] = {
    Ecosystem.PYTHON: PyPIClient,
    Ecosystem.NODE: NpmClient,
    Ecosystem.RUST: CratesClient,
    Ecosystem.GO: GoClient,
    Ecosystem.RUBY: RubyGemsClient,
}


def get_client(ecosystem: Ecosystem, base_url: str | None = None) -> RegistryClient:
    """Get a registry client for the given ecosystem."""
    client_cls = REGISTRY_MAP[ecosystem]
    if base_url:
        return client_cls(base_url=base_url)
    return client_cls()


__all__ = [
    "CratesClient",
    "GoClient",
    "NpmClient",
    "PyPIClient",
    "RegistryClient",
    "RubyGemsClient",
    "get_client",
]
