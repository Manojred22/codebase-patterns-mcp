"""
Python parser — extracts functions, methods, and classes from Python source files.
"""

from typing import List, Optional

from .base import BaseParser
from ..models import CodeFunction


class PythonParser(BaseParser):
    """Parse Python source code using tree-sitter."""

    def __init__(self):
        super().__init__("python")

    def parse_file(self, file_path: str, content: str) -> List[CodeFunction]:
        tree = self._parse_tree(content)
        root = tree.root_node

        functions: List[CodeFunction] = []
        seen_nodes = set()

        for node in self._traverse(root):
            if id(node) in seen_nodes:
                continue

            if node.type == "decorated_definition":
                inner = self._get_inner_definition(node)
                if inner and inner.type == "function_definition":
                    func = self._extract_function(inner, content, file_path, decorator_node=node)
                    if func:
                        functions.append(func)
                        seen_nodes.add(id(node))
                        seen_nodes.add(id(inner))
                elif inner and inner.type == "class_definition":
                    func = self._extract_class(inner, content, file_path, decorator_node=node)
                    if func:
                        functions.append(func)
                        seen_nodes.add(id(node))
                        seen_nodes.add(id(inner))

            elif node.type == "function_definition":
                # Skip if parent is decorated_definition (already handled)
                if node.parent and node.parent.type == "decorated_definition":
                    continue
                func = self._extract_function(node, content, file_path)
                if func:
                    functions.append(func)
                    seen_nodes.add(id(node))

            elif node.type == "class_definition":
                if node.parent and node.parent.type == "decorated_definition":
                    continue
                func = self._extract_class(node, content, file_path)
                if func:
                    functions.append(func)
                    seen_nodes.add(id(node))

        return functions

    def _extract_function(self, node, content: str, file_path: str,
                          decorator_node=None) -> Optional[CodeFunction]:
        try:
            name = self._get_name(node, content)
            if not name:
                return None

            decorators = self._get_decorators(decorator_node, content) if decorator_node else []
            docstring = self._get_python_docstring(node, content)
            class_name = self._get_enclosing_class(node, content)

            # Full code includes decorators
            code_node = decorator_node if decorator_node else node
            full_code = self._node_text(code_node, content)

            start_line = code_node.start_point[0] + 1
            end_line = code_node.end_point[0] + 1

            signature = self._get_signature(node, content)

            body_node = self._find_child_by_type(node, "block")
            body = self._node_text(body_node, content) if body_node else ""

            is_method = class_name is not None
            is_exported = not name.startswith("_")

            # Determine construct type
            construct_type = "method" if is_method else "function"

            return CodeFunction(
                name=name,
                signature=signature,
                body=body,
                full_code=full_code,
                docstring=docstring,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                language="python",
                class_name=class_name,
                decorators=decorators,
                is_exported=is_exported,
                construct_type=construct_type,
            )
        except Exception:
            return None

    def _extract_class(self, node, content: str, file_path: str,
                       decorator_node=None) -> Optional[CodeFunction]:
        try:
            name = self._get_name(node, content)
            if not name:
                return None

            decorators = self._get_decorators(decorator_node, content) if decorator_node else []
            docstring = self._get_python_docstring(node, content)

            code_node = decorator_node if decorator_node else node
            full_code = self._node_text(code_node, content)

            start_line = code_node.start_point[0] + 1
            end_line = code_node.end_point[0] + 1

            signature = self._get_signature(node, content)

            body_node = self._find_child_by_type(node, "block")
            body = self._node_text(body_node, content) if body_node else ""

            is_exported = not name.startswith("_")

            return CodeFunction(
                name=name,
                signature=signature,
                body=body,
                full_code=full_code,
                docstring=docstring,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                language="python",
                decorators=decorators,
                is_exported=is_exported,
                construct_type="class",
            )
        except Exception:
            return None

    # ---- helpers ----

    def _get_name(self, node, content: str) -> Optional[str]:
        name_node = self._find_child_by_type(node, "identifier")
        return self._node_text(name_node, content) if name_node else None

    def _get_signature(self, node, content: str) -> str:
        """Get the def/class line (up to the colon)."""
        b = self._content_bytes
        sig_end = b.find(b':', node.start_byte)
        if sig_end == -1 or sig_end > node.end_byte:
            sig_end = b.find(b'\n', node.start_byte)
            if sig_end == -1:
                sig_end = node.end_byte
        return b[node.start_byte:sig_end + 1].decode("utf-8", errors="replace").strip()

    def _get_inner_definition(self, decorated_node):
        """Get the function_definition or class_definition inside a decorated_definition."""
        for child in decorated_node.children:
            if child.type in ("function_definition", "class_definition"):
                return child
        return None

    def _get_decorators(self, decorator_node, content: str) -> List[str]:
        decorators = []
        if decorator_node and decorator_node.type == "decorated_definition":
            for child in decorator_node.children:
                if child.type == "decorator":
                    decorators.append(self._node_text(child, content))
        return decorators

    def _get_python_docstring(self, node, content: str) -> Optional[str]:
        """Extract Python docstring (first expression_statement > string in body block)."""
        body = self._find_child_by_type(node, "block")
        if body and body.children:
            first_stmt = body.children[0]
            if first_stmt.type == "expression_statement":
                for child in first_stmt.children:
                    if child.type == "string":
                        return self._node_text(child, content)
        # Fall back to preceding comments
        return self._get_preceding_comments(node, content)

    def _get_enclosing_class(self, node, content: str) -> Optional[str]:
        """Walk up to find enclosing class_definition."""
        current = node.parent
        while current:
            if current.type == "class_definition":
                name_node = self._find_child_by_type(current, "identifier")
                if name_node:
                    return self._node_text(name_node, content)
            current = current.parent
        return None
