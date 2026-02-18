"""
Multi-language parser package.
"""

from .registry import ParserRegistry, EXTENSION_MAP
from .base import BaseParser
from .go_parser import GoParser
from .typescript_parser import TypeScriptParser

__all__ = ["ParserRegistry", "EXTENSION_MAP", "BaseParser", "GoParser", "TypeScriptParser"]
