"""Tests for Python dependency parsers."""

from pathlib import Path

from sup.parsers.python import PythonParser

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_parse_requirements_txt() -> None:
    parser = PythonParser()
    result = parser.parse(FIXTURES / "requirements.txt")
    assert ("requests", "2.31.0") in result
    assert ("click", "8.1.7") in result
    assert ("numpy", "1.26.0") in result
    assert ("rich", "13.7.0") in result
    assert len(result) == 4


def test_parse_pyproject_toml() -> None:
    parser = PythonParser()
    result = parser.parse(FIXTURES / "pyproject.toml")
    assert ("click", "8.1.7") in result
    assert ("rich", "13.0") in result
    assert ("httpx", "0.27") in result


def test_parse_poetry_lock() -> None:
    parser = PythonParser()
    result = parser.parse(FIXTURES / "poetry.lock")
    assert ("requests", "2.31.0") in result
    assert ("urllib3", "2.1.0") in result
    assert len(result) == 2


def test_parse_pipfile_lock() -> None:
    parser = PythonParser()
    result = parser.parse(FIXTURES / "Pipfile.lock")
    assert ("requests", "2.31.0") in result
    assert ("click", "8.1.7") in result
    assert ("pytest", "8.0.0") in result
    assert len(result) == 3
