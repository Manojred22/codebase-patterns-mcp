"""
Base parser with shared tree-sitter helpers.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import tree_sitter

from ..models import CodeFunction


class BaseParser(ABC):
    """Abstract base for language-specific tree-sitter parsers."""

    def __init__(self, language_name: str):
        from tree_sitter_languages import get_language
        language = get_language(language_name)
        self.parser = tree_sitter.Parser()
        self.parser.set_language(language)
        self.language_name = language_name

    @abstractmethod
    def parse_file(self, file_path: str, content: str) -> List[CodeFunction]:
        """Extract all functions/methods/classes from a source file."""
        ...

    def _traverse(self, node):
        """Recursively traverse AST yielding all nodes."""
        yield node
        for child in node.children:
            yield from self._traverse(child)

    def _node_text(self, node, content: str) -> str:
        """Get the source text for a tree-sitter node."""
        return content[node.start_byte:node.end_byte]

    def _get_preceding_comments(self, node, content: str) -> Optional[str]:
        """Get comment block immediately above a node."""
        comments = []
        current = node.prev_sibling

        while current and current.type in self._comment_node_types():
            comment_text = self._node_text(current, content)
            comments.insert(0, comment_text)
            current = current.prev_sibling

        return "\n".join(comments) if comments else None

    def _comment_node_types(self) -> set:
        """Node types that represent comments. Override per language if needed."""
        return {"comment"}

    def _find_child_by_type(self, node, type_name: str):
        """Find first direct child of given type."""
        for child in node.children:
            if child.type == type_name:
                return child
        return None

    def _find_children_by_type(self, node, type_name: str) -> list:
        """Find all direct children of given type."""
        return [child for child in node.children if child.type == type_name]

    def _find_ancestor_by_type(self, node, type_name: str):
        """Walk up the tree to find an ancestor of the given type."""
        current = node.parent
        while current:
            if current.type == type_name:
                return current
            current = current.parent
        return None
