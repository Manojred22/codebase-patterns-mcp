"""
Go code parser using tree-sitter.
Extracts functions with metadata for embedding.
"""

from dataclasses import dataclass
from typing import List, Optional
import tree_sitter
from tree_sitter_languages import get_language


@dataclass
class GoFunction:
    """Represents an extracted Go function"""
    name: str
    signature: str
    body: str
    full_code: str
    docstring: Optional[str]
    file_path: str
    start_line: int
    end_line: int
    receiver: Optional[str] = None  # For methods: (r *Receiver)


class GoParser:
    """Parse Go source code and extract functions"""

    def __init__(self):
        language = get_language("go")
        self.parser = tree_sitter.Parser()
        self.parser.set_language(language)

    def parse_file(self, file_path: str, content: str) -> List[GoFunction]:
        """
        Extract all functions from a Go file

        Args:
            file_path: Path to the Go file (for metadata)
            content: File content as string

        Returns:
            List of GoFunction objects
        """
        tree = self.parser.parse(bytes(content, "utf8"))
        root = tree.root_node

        functions = []

        # Find all function and method declarations
        for node in self._traverse(root):
            if node.type in ["function_declaration", "method_declaration"]:
                func = self._extract_function(node, content, file_path)
                if func:
                    functions.append(func)

        return functions

    def _extract_function(self, node, content: str, file_path: str) -> Optional[GoFunction]:
        """Extract function details from AST node"""
        try:
            # Get function name
            name = self._get_function_name(node, content)
            if not name:
                return None

            # Get receiver for methods
            receiver = self._get_receiver(node, content)

            # Get docstring (comment above function)
            docstring = self._get_docstring(node, content)

            # Get full function code
            full_code = content[node.start_byte:node.end_byte]

            # Get signature (first line)
            signature_end = content.find('\n', node.start_byte)
            if signature_end == -1:
                signature_end = node.end_byte
            signature = content[node.start_byte:signature_end].strip()

            # Get body (everything after signature)
            body_start = content.find('{', node.start_byte)
            if body_start != -1:
                body = content[body_start:node.end_byte]
            else:
                body = full_code

            return GoFunction(
                name=name,
                signature=signature,
                body=body,
                full_code=full_code,
                docstring=docstring,
                file_path=file_path,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                receiver=receiver
            )

        except Exception as e:
            print(f"Error extracting function: {e}")
            return None

    def _get_function_name(self, node, content: str) -> Optional[str]:
        """Extract function/method name"""
        for child in node.children:
            if child.type == "identifier":
                return content[child.start_byte:child.end_byte]
        return None

    def _get_receiver(self, node, content: str) -> Optional[str]:
        """Extract receiver for methods (e.g., (s *Service))"""
        if node.type != "method_declaration":
            return None

        for child in node.children:
            if child.type == "parameter_list":
                # This is the receiver
                return content[child.start_byte:child.end_byte]
        return None

    def _get_docstring(self, node, content: str) -> Optional[str]:
        """Extract comment block above function"""
        # Get previous sibling(s) - could be multiple comment lines
        comments = []
        current = node.prev_sibling

        while current and current.type == "comment":
            comment_text = content[current.start_byte:current.end_byte]
            comments.insert(0, comment_text)  # Insert at beginning to maintain order
            current = current.prev_sibling

        if comments:
            return "\n".join(comments)
        return None

    def _traverse(self, node):
        """Recursively traverse AST"""
        yield node
        for child in node.children:
            yield from self._traverse(child)


if __name__ == "__main__":
    # Test the parser
    import sys

    if len(sys.argv) < 2:
        print("Usage: python parser.py <go_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    with open(file_path, 'r') as f:
        content = f.read()

    parser = GoParser()
    functions = parser.parse_file(file_path, content)

    print(f"\nFound {len(functions)} functions in {file_path}:\n")
    for func in functions:
        print(f"  {func.name} ({func.start_line}-{func.end_line})")
        if func.docstring:
            print(f"    Doc: {func.docstring[:50]}...")
