"""
Go parser — extracts functions and methods from Go source files.
"""

from typing import List, Optional

from .base import BaseParser
from ..models import CodeFunction


class GoParser(BaseParser):
    """Parse Go source code and extract functions/methods."""

    def __init__(self):
        super().__init__("go")

    def parse_file(self, file_path: str, content: str) -> List[CodeFunction]:
        tree = self._parse_tree(content)
        root = tree.root_node

        functions = []
        for node in self._traverse(root):
            if node.type in ("function_declaration", "method_declaration"):
                func = self._extract_function(node, content, file_path)
                if func:
                    functions.append(func)

        return functions

    def _extract_function(self, node, content: str, file_path: str) -> Optional[CodeFunction]:
        try:
            name = self._get_function_name(node, content)
            if not name:
                return None

            receiver = self._get_receiver(node, content)
            docstring = self._get_preceding_comments(node, content)
            full_code = self._node_text(node, content)

            # Signature: first line
            b = self._content_bytes
            signature_end = b.find(b'\n', node.start_byte)
            if signature_end == -1:
                signature_end = node.end_byte
            signature = b[node.start_byte:signature_end].decode("utf-8", errors="replace").strip()

            # Body: everything from opening brace
            body_start = b.find(b'{', node.start_byte)
            body = b[body_start:node.end_byte].decode("utf-8", errors="replace") if body_start != -1 else full_code

            is_method = receiver is not None
            is_exported = name[0].isupper() if name else True

            return CodeFunction(
                name=name,
                signature=signature,
                body=body,
                full_code=full_code,
                docstring=docstring,
                file_path=file_path,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                language="go",
                receiver=receiver,
                is_exported=is_exported,
                construct_type="method" if is_method else "function",
            )
        except Exception:
            return None

    def _get_function_name(self, node, content: str) -> Optional[str]:
        for child in node.children:
            if child.type in ("identifier", "field_identifier"):
                return self._node_text(child, content)
        return None

    def _get_receiver(self, node, content: str) -> Optional[str]:
        if node.type != "method_declaration":
            return None
        for child in node.children:
            if child.type == "parameter_list":
                return self._node_text(child, content)
        return None
