"""
JavaScript parser — extracts functions, classes, methods, and arrow functions.
"""

from typing import List, Optional

from .base import BaseParser
from ..models import CodeFunction


class JavaScriptParser(BaseParser):
    """Parse JavaScript source code using tree-sitter."""

    def __init__(self):
        super().__init__("javascript")

    def parse_file(self, file_path: str, content: str) -> List[CodeFunction]:
        tree = self.parser.parse(bytes(content, "utf8"))
        root = tree.root_node

        functions: List[CodeFunction] = []
        seen_nodes = set()

        for node in self._traverse(root):
            if id(node) in seen_nodes:
                continue

            if node.type == "function_declaration":
                func = self._extract_function_declaration(node, content, file_path)
                if func:
                    functions.append(func)
                    seen_nodes.add(id(node))

            elif node.type == "class_declaration":
                func = self._extract_class(node, content, file_path)
                if func:
                    functions.append(func)
                    seen_nodes.add(id(node))

            elif node.type == "method_definition":
                func = self._extract_method(node, content, file_path)
                if func:
                    functions.append(func)
                    seen_nodes.add(id(node))

            elif node.type == "variable_declarator":
                # Check for arrow functions: const foo = (...) => { ... }
                func = self._extract_arrow_function(node, content, file_path)
                if func:
                    functions.append(func)
                    seen_nodes.add(id(node))

        return functions

    def _extract_function_declaration(self, node, content: str, file_path: str) -> Optional[CodeFunction]:
        try:
            name = self._get_name(node, content)
            if not name:
                return None

            docstring = self._get_preceding_comments(node, content)
            is_exported = self._is_exported(node)

            # If wrapped in export_statement, include that
            export_node = node.parent if node.parent and node.parent.type == "export_statement" else None
            code_node = export_node if export_node else node
            full_code = self._node_text(code_node, content)

            signature = self._get_signature_line(node, content)

            body_node = self._find_child_by_type(node, "statement_block")
            body = self._node_text(body_node, content) if body_node else ""

            return CodeFunction(
                name=name,
                signature=signature,
                body=body,
                full_code=full_code,
                docstring=docstring,
                file_path=file_path,
                start_line=code_node.start_point[0] + 1,
                end_line=code_node.end_point[0] + 1,
                language="javascript",
                is_exported=is_exported,
                construct_type="function",
            )
        except Exception:
            return None

    def _extract_class(self, node, content: str, file_path: str) -> Optional[CodeFunction]:
        try:
            name = self._get_name(node, content)
            if not name:
                return None

            docstring = self._get_preceding_comments(node, content)
            is_exported = self._is_exported(node)

            export_node = node.parent if node.parent and node.parent.type == "export_statement" else None
            code_node = export_node if export_node else node
            full_code = self._node_text(code_node, content)

            signature = self._get_signature_line(node, content)

            body_node = self._find_child_by_type(node, "class_body")
            body = self._node_text(body_node, content) if body_node else ""

            return CodeFunction(
                name=name,
                signature=signature,
                body=body,
                full_code=full_code,
                docstring=docstring,
                file_path=file_path,
                start_line=code_node.start_point[0] + 1,
                end_line=code_node.end_point[0] + 1,
                language="javascript",
                is_exported=is_exported,
                construct_type="class",
            )
        except Exception:
            return None

    def _extract_method(self, node, content: str, file_path: str) -> Optional[CodeFunction]:
        try:
            # method_definition has property_identifier as name
            name_node = self._find_child_by_type(node, "property_identifier")
            if not name_node:
                return None
            name = self._node_text(name_node, content)

            docstring = self._get_preceding_comments(node, content)
            class_name = self._get_enclosing_class(node, content)
            full_code = self._node_text(node, content)
            signature = self._get_signature_line(node, content)

            body_node = self._find_child_by_type(node, "statement_block")
            body = self._node_text(body_node, content) if body_node else ""

            construct_type = "constructor" if name == "constructor" else "method"

            return CodeFunction(
                name=name,
                signature=signature,
                body=body,
                full_code=full_code,
                docstring=docstring,
                file_path=file_path,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                language="javascript",
                class_name=class_name,
                is_exported=True,  # methods are accessible if class is
                construct_type=construct_type,
            )
        except Exception:
            return None

    def _extract_arrow_function(self, node, content: str, file_path: str) -> Optional[CodeFunction]:
        """Extract arrow function from variable_declarator: const foo = () => { ... }"""
        try:
            # Check if this variable_declarator has an arrow_function child
            arrow_node = self._find_child_by_type(node, "arrow_function")
            if not arrow_node:
                return None

            name_node = self._find_child_by_type(node, "identifier")
            if not name_node:
                return None
            name = self._node_text(name_node, content)

            # Get the full variable declaration (including const/let/var and export)
            decl_node = node.parent  # lexical_declaration or variable_declaration
            export_node = None
            if decl_node and decl_node.parent and decl_node.parent.type == "export_statement":
                export_node = decl_node.parent

            code_node = export_node if export_node else (decl_node if decl_node else node)
            full_code = self._node_text(code_node, content)

            docstring = self._get_preceding_comments(code_node, content)
            is_exported = self._is_exported(node)

            signature = self._get_signature_line(code_node, content)

            body_node = self._find_child_by_type(arrow_node, "statement_block")
            body = self._node_text(body_node, content) if body_node else self._node_text(arrow_node, content)

            # Detect React component (uppercase name + returns JSX)
            construct_type = "function"
            if name and name[0].isupper() and self._has_jsx(arrow_node, content):
                construct_type = "function"  # React component, still a function
            elif name and name.startswith("use"):
                construct_type = "function"  # React hook

            return CodeFunction(
                name=name,
                signature=signature,
                body=body,
                full_code=full_code,
                docstring=docstring,
                file_path=file_path,
                start_line=code_node.start_point[0] + 1,
                end_line=code_node.end_point[0] + 1,
                language="javascript",
                is_exported=is_exported,
                construct_type=construct_type,
            )
        except Exception:
            return None

    # ---- helpers ----

    def _get_name(self, node, content: str) -> Optional[str]:
        name_node = self._find_child_by_type(node, "identifier")
        return self._node_text(name_node, content) if name_node else None

    def _get_signature_line(self, node, content: str) -> str:
        sig_end = content.find('\n', node.start_byte)
        if sig_end == -1:
            sig_end = node.end_byte
        return content[node.start_byte:sig_end].strip()

    def _is_exported(self, node) -> bool:
        """Check if node or any ancestor is inside an export_statement."""
        current = node.parent
        while current:
            if current.type == "export_statement":
                return True
            current = current.parent
        return False

    def _get_enclosing_class(self, node, content: str) -> Optional[str]:
        class_node = self._find_ancestor_by_type(node, "class_declaration")
        if class_node:
            name_node = self._find_child_by_type(class_node, "identifier")
            if name_node:
                return self._node_text(name_node, content)
        return None

    def _has_jsx(self, node, content: str) -> bool:
        """Check if node tree contains JSX elements."""
        for child in self._traverse(node):
            if child.type in ("jsx_element", "jsx_self_closing_element", "jsx_fragment"):
                return True
        return False
