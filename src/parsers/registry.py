"""
Parser registry — maps file extensions to language parsers.
"""

from typing import Dict, Optional, Set

from .base import BaseParser

EXTENSION_MAP: Dict[str, str] = {
    ".go": "go",
    ".java": "java",
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
}


class ParserRegistry:
    """Lazy-loading registry of language parsers."""

    def __init__(self):
        self._parsers: Dict[str, BaseParser] = {}

    def get_parser(self, ext: str) -> Optional[BaseParser]:
        """Get parser for a file extension. Returns None if unsupported."""
        language = EXTENSION_MAP.get(ext)
        if not language:
            return None

        if language not in self._parsers:
            self._parsers[language] = self._create_parser(language)

        return self._parsers[language]

    def get_language(self, ext: str) -> Optional[str]:
        """Get language name for a file extension (tsx reports as typescript)."""
        lang = EXTENSION_MAP.get(ext)
        if lang == "tsx":
            return "typescript"
        return lang

    def supported_extensions(self) -> Set[str]:
        """Return set of supported file extensions."""
        return set(EXTENSION_MAP.keys())

    def _create_parser(self, language: str) -> BaseParser:
        if language == "go":
            from .go_parser import GoParser
            return GoParser()
        elif language == "java":
            from .java_parser import JavaParser
            return JavaParser()
        elif language == "python":
            from .python_parser import PythonParser
            return PythonParser()
        elif language == "javascript":
            from .javascript_parser import JavaScriptParser
            return JavaScriptParser()
        elif language == "typescript":
            from .typescript_parser import TypeScriptParser
            return TypeScriptParser(tsx=False)
        elif language == "tsx":
            from .typescript_parser import TypeScriptParser
            return TypeScriptParser(tsx=True)
        else:
            raise ValueError(f"No parser for language: {language}")
