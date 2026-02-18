"""
TypeScript parser — extends JavaScript parser with interfaces, decorators, and type annotations.
Uses the 'typescript' grammar for .ts and 'tsx' grammar for .tsx files.
"""

from typing import List, Optional

from .base import BaseParser
from ..models import CodeFunction


class TypeScriptParser(BaseParser):
    """Parse TypeScript source code using tree-sitter."""

    def __init__(self, tsx: bool = False):
        super().__init__("tsx" if tsx else "typescript")
        self._tsx = tsx

    def parse_file(self, file_path: str, content: str) -> List[CodeFunction]:
        tree = self._parse_tree(content)
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
                func = self._extract_arrow_function(node, content, file_path)
                if func:
                    functions.append(func)
                    seen_nodes.add(id(node))

            elif node.type == "interface_declaration":
                func = self._extract_interface(node, content, file_path)
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
                language="typescript",
                is_exported=is_exported,
                construct_type="function",
            )
        except Exception:
            return None

    def _extract_class(self, node, content: str, file_path: str) -> Optional[CodeFunction]:
        try:
            # TypeScript uses type_identifier for class names
            name = self._get_name(node, content)
            if not name:
                return None

            docstring = self._get_preceding_comments(node, content)
            is_exported = self._is_exported(node)
            decorators = self._get_class_decorators(node, content)

            # Include the full export_statement (which may contain decorators)
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
                language="typescript",
                decorators=decorators,
                is_exported=is_exported,
                construct_type="class",
            )
        except Exception:
            return None

    def _extract_method(self, node, content: str, file_path: str) -> Optional[CodeFunction]:
        try:
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

            # Check for decorators on the method (TypeScript/NestJS style)
            decorators = self._get_method_decorators(node, content)

            return CodeFunction(
                name=name,
                signature=signature,
                body=body,
                full_code=full_code,
                docstring=docstring,
                file_path=file_path,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                language="typescript",
                class_name=class_name,
                decorators=decorators,
                is_exported=True,
                construct_type=construct_type,
            )
        except Exception:
            return None

    def _extract_arrow_function(self, node, content: str, file_path: str) -> Optional[CodeFunction]:
        try:
            arrow_node = self._find_child_by_type(node, "arrow_function")
            if not arrow_node:
                return None

            name_node = self._find_child_by_type(node, "identifier")
            if not name_node:
                return None
            name = self._node_text(name_node, content)

            decl_node = node.parent
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

            return CodeFunction(
                name=name,
                signature=signature,
                body=body,
                full_code=full_code,
                docstring=docstring,
                file_path=file_path,
                start_line=code_node.start_point[0] + 1,
                end_line=code_node.end_point[0] + 1,
                language="typescript",
                is_exported=is_exported,
                construct_type="function",
            )
        except Exception:
            return None

    def _extract_interface(self, node, content: str, file_path: str) -> Optional[CodeFunction]:
        try:
            # interface name is a type_identifier
            name = self._get_name(node, content)
            if not name:
                return None

            docstring = self._get_preceding_comments(node, content)
            is_exported = self._is_exported(node)

            export_node = node.parent if node.parent and node.parent.type == "export_statement" else None
            code_node = export_node if export_node else node
            full_code = self._node_text(code_node, content)
            signature = self._get_signature_line(node, content)

            body_node = self._find_child_by_type(node, "object_type")
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
                language="typescript",
                is_exported=is_exported,
                construct_type="interface",
            )
        except Exception:
            return None

    # ---- helpers ----

    def _get_name(self, node, content: str) -> Optional[str]:
        """Get name — TypeScript uses type_identifier for classes/interfaces."""
        for type_name in ("identifier", "type_identifier"):
            name_node = self._find_child_by_type(node, type_name)
            if name_node:
                return self._node_text(name_node, content)
        return None

    def _get_signature_line(self, node, content: str) -> str:
        b = self._content_bytes
        sig_end = b.find(b'\n', node.start_byte)
        if sig_end == -1:
            sig_end = node.end_byte
        return b[node.start_byte:sig_end].decode("utf-8", errors="replace").strip()

    def _is_exported(self, node) -> bool:
        current = node.parent
        while current:
            if current.type == "export_statement":
                return True
            current = current.parent
        return False

    def _get_enclosing_class(self, node, content: str) -> Optional[str]:
        class_node = self._find_ancestor_by_type(node, "class_declaration")
        if class_node:
            name = self._get_name(class_node, content)
            if name:
                return name
        return None

    def _get_class_decorators(self, node, content: str) -> List[str]:
        """Get decorators from the parent export_statement (NestJS/Angular style)."""
        decorators = []
        parent = node.parent
        if parent and parent.type == "export_statement":
            for child in parent.children:
                if child.type == "decorator":
                    decorators.append(self._node_text(child, content))
        return decorators

    def _get_method_decorators(self, node, content: str) -> List[str]:
        """Get decorators preceding a method_definition inside a class body."""
        decorators = []
        prev = node.prev_sibling
        while prev and prev.type == "decorator":
            decorators.insert(0, self._node_text(prev, content))
            prev = prev.prev_sibling
        return decorators

    def _has_jsx(self, node, content: str) -> bool:
        for child in self._traverse(node):
            if child.type in ("jsx_element", "jsx_self_closing_element", "jsx_fragment"):
                return True
        return False
