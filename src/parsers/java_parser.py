"""
Java parser — extracts classes, methods, constructors, and interfaces.
"""

from typing import List, Optional

from .base import BaseParser
from ..models import CodeFunction


class JavaParser(BaseParser):
    """Parse Java source code using tree-sitter."""

    def __init__(self):
        super().__init__("java")

    def _comment_node_types(self) -> set:
        return {"comment", "line_comment", "block_comment"}

    def parse_file(self, file_path: str, content: str) -> List[CodeFunction]:
        tree = self.parser.parse(bytes(content, "utf8"))
        root = tree.root_node

        functions: List[CodeFunction] = []
        seen_nodes = set()

        for node in self._traverse(root):
            if id(node) in seen_nodes:
                continue

            if node.type == "method_declaration":
                func = self._extract_method(node, content, file_path)
                if func:
                    functions.append(func)
                    seen_nodes.add(id(node))

            elif node.type == "constructor_declaration":
                func = self._extract_constructor(node, content, file_path)
                if func:
                    functions.append(func)
                    seen_nodes.add(id(node))

            elif node.type == "class_declaration":
                func = self._extract_class(node, content, file_path)
                if func:
                    functions.append(func)
                    seen_nodes.add(id(node))

            elif node.type == "interface_declaration":
                func = self._extract_interface(node, content, file_path)
                if func:
                    functions.append(func)
                    seen_nodes.add(id(node))

        return functions

    def _extract_method(self, node, content: str, file_path: str) -> Optional[CodeFunction]:
        try:
            name = self._get_name(node, content)
            if not name:
                return None

            annotations = self._get_annotations(node, content)
            modifiers = self._get_modifiers(node, content)
            docstring = self._get_javadoc(node, content)
            class_name = self._get_enclosing_class(node, content)
            # tree-sitter already includes modifiers/annotations in the node range
            full_code = self._node_text(node, content)

            signature = self._get_signature_line(node, content)

            body_node = self._find_child_by_type(node, "block")
            body = self._node_text(body_node, content) if body_node else ""

            is_exported = "public" in modifiers

            return CodeFunction(
                name=name,
                signature=signature,
                body=body,
                full_code=full_code,
                docstring=docstring,
                file_path=file_path,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                language="java",
                class_name=class_name,
                decorators=annotations,
                modifiers=modifiers,
                is_exported=is_exported,
                construct_type="method",
            )
        except Exception:
            return None

    def _extract_constructor(self, node, content: str, file_path: str) -> Optional[CodeFunction]:
        try:
            name = self._get_name(node, content)
            if not name:
                return None

            annotations = self._get_annotations(node, content)
            modifiers = self._get_modifiers(node, content)
            docstring = self._get_javadoc(node, content)
            class_name = self._get_enclosing_class(node, content)
            full_code = self._node_text(node, content)

            signature = self._get_signature_line(node, content)

            body_node = self._find_child_by_type(node, "constructor_body")
            body = self._node_text(body_node, content) if body_node else ""

            return CodeFunction(
                name=name,
                signature=signature,
                body=body,
                full_code=full_code,
                docstring=docstring,
                file_path=file_path,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                language="java",
                class_name=class_name,
                decorators=annotations,
                modifiers=modifiers,
                is_exported="public" in modifiers,
                construct_type="constructor",
            )
        except Exception:
            return None

    def _extract_class(self, node, content: str, file_path: str) -> Optional[CodeFunction]:
        try:
            name = self._get_name(node, content)
            if not name:
                return None

            annotations = self._get_annotations(node, content)
            modifiers = self._get_modifiers(node, content)
            docstring = self._get_javadoc(node, content)
            full_code = self._node_text(node, content)

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
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                language="java",
                decorators=annotations,
                modifiers=modifiers,
                is_exported="public" in modifiers,
                construct_type="class",
            )
        except Exception:
            return None

    def _extract_interface(self, node, content: str, file_path: str) -> Optional[CodeFunction]:
        try:
            name = self._get_name(node, content)
            if not name:
                return None

            annotations = self._get_annotations(node, content)
            modifiers = self._get_modifiers(node, content)
            docstring = self._get_javadoc(node, content)
            full_code = self._node_text(node, content)

            signature = self._get_signature_line(node, content)

            body_node = self._find_child_by_type(node, "interface_body")
            body = self._node_text(body_node, content) if body_node else ""

            return CodeFunction(
                name=name,
                signature=signature,
                body=body,
                full_code=full_code,
                docstring=docstring,
                file_path=file_path,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                language="java",
                decorators=annotations,
                modifiers=modifiers,
                is_exported="public" in modifiers,
                construct_type="interface",
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

    def _get_modifiers(self, node, content: str) -> List[str]:
        modifiers = []
        mod_node = self._find_child_by_type(node, "modifiers")
        if mod_node:
            for child in mod_node.children:
                if child.type in ("public", "private", "protected", "static",
                                  "abstract", "final", "synchronized", "native"):
                    modifiers.append(child.type)
                # Also check text for keyword nodes
                text = self._node_text(child, content)
                if text in ("public", "private", "protected", "static",
                            "abstract", "final", "synchronized", "native") and text not in modifiers:
                    modifiers.append(text)
        return modifiers

    def _get_annotations(self, node, content: str) -> List[str]:
        annotations = []
        mod_node = self._find_child_by_type(node, "modifiers")
        if mod_node:
            for child in mod_node.children:
                if child.type in ("marker_annotation", "annotation"):
                    annotations.append(self._node_text(child, content))
        return annotations

    def _get_javadoc(self, node, content: str) -> Optional[str]:
        """Get Javadoc (block comment starting with /**) above the node."""
        current = node.prev_sibling
        while current:
            if current.type == "block_comment":
                text = self._node_text(current, content)
                if text.startswith("/**"):
                    return text
            elif current.type in ("line_comment", "comment"):
                current = current.prev_sibling
                continue
            else:
                break
            current = current.prev_sibling
        return self._get_preceding_comments(node, content)

    def _get_enclosing_class(self, node, content: str) -> Optional[str]:
        class_node = self._find_ancestor_by_type(node, "class_declaration")
        if class_node:
            name_node = self._find_child_by_type(class_node, "identifier")
            if name_node:
                return self._node_text(name_node, content)
        return None
