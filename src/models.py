"""
Unified data models for multi-language code indexing.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CodeFunction:
    """Represents an extracted code function/method/class from any language."""
    name: str
    signature: str
    body: str
    full_code: str
    docstring: Optional[str]
    file_path: str
    start_line: int
    end_line: int
    language: str  # "go", "java", "python", "javascript"
    receiver: Optional[str] = None  # Go methods
    class_name: Optional[str] = None  # Java/Python/JS: enclosing class
    decorators: List[str] = field(default_factory=list)  # Python decorators, Java annotations
    modifiers: List[str] = field(default_factory=list)  # Java: public/private/static
    is_exported: bool = True
    construct_type: str = "function"  # "function", "method", "class", "constructor", "interface"


# Backward compat alias
GoFunction = CodeFunction


@dataclass
class IndexedFunction:
    """Function with metadata ready for embedding and storage."""
    id: str  # Unique ID: repo_name/file_path:function_name
    content: str  # Embedding text (metadata prefix + full code, possibly truncated for huge functions)
    full_code: str  # Complete source code (always stored, returned in search)
    metadata: Dict  # Additional info (file, line numbers, language, patterns, etc.)
