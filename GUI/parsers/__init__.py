"""
MusicCode GUI — Parsers Package
AST-based parsing of MusicCode Python scripts into ProjectModel.
"""

from .musiccode_parser import MusicCodeParser, parse_musiccode_file

__all__ = [
    "MusicCodeParser",
    "parse_musiccode_file",
]