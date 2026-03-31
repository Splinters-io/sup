"""Dependency file parsers for all supported ecosystems."""

from sup.parsers.detect import detect_ecosystem
from sup.parsers.base import DependencyParser, parse_dependencies

__all__ = ["DependencyParser", "detect_ecosystem", "parse_dependencies"]
