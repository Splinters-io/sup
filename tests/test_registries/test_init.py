"""Test for registries __init__ get_client with custom base_url."""

from sup.models import Ecosystem
from sup.registries import get_client


def test_get_client_with_custom_url() -> None:
    client = get_client(Ecosystem.PYTHON, base_url="https://custom.pypi.org")
    assert client._base_url == "https://custom.pypi.org"
