"""
Indexer module - crawls repos, extracts functions, creates embeddings.
Indexes ONLY production Go code (excludes tests, configs, generated files).
"""

import os
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass
from tqdm import tqdm
import json

from .parser import GoParser, GoFunction


@dataclass
class IndexedFunction:
    """Function with metadata ready for embedding"""
    id: str  # Unique ID: repo_name/file_path:function_name
    content: str  # What gets embedded
    metadata: Dict  # Additional info (file, line numbers, etc.)


class CodeIndexer:
    """Crawls repositories and extracts functions from production code"""

    def __init__(self, repos_path: str):
        self.repos_path = Path(repos_path)
        self.parser = GoParser()
        self.stats = {
            "total_files": 0,
            "skipped_tests": 0,
            "skipped_vendor": 0,
            "skipped_generated": 0,
            "skipped_other": 0,
            "indexed_files": 0,
            "total_functions": 0,
        }

    def index_all_repos(self) -> List[IndexedFunction]:
        """
        Index all Go production code in all repositories

        Returns:
            List of IndexedFunction objects ready for embedding
        """
        print(f"\n📂 Indexing production Go code from: {self.repos_path}")
        print("   ℹ️  Excluding: tests, vendor, mocks, generated files, configs\n")

        all_functions = []
        repos = [d for d in self.repos_path.iterdir() if d.is_dir() and not d.name.startswith('.')]

        for repo in repos:
            print(f"\n  📁 {repo.name}")
            repo_functions = self.index_repo(repo)
            all_functions.extend(repo_functions)
            print(f"     ✓ {len(repo_functions)} functions")

        self._print_stats()
        return all_functions

    def index_repo(self, repo_path: Path) -> List[IndexedFunction]:
        """Index all production Go files in a single repository"""
        functions = []

        # Find all .go files
        go_files = list(repo_path.rglob("*.go"))
        self.stats["total_files"] += len(go_files)

        # Filter to production code only
        production_files = [f for f in go_files if self._should_index_file(f)]
        self.stats["indexed_files"] += len(production_files)

        for go_file in tqdm(production_files, desc=f"  {repo_path.name}", leave=False):
            try:
                file_functions = self._index_file(go_file, repo_path)
                functions.extend(file_functions)
                self.stats["total_functions"] += len(file_functions)
            except Exception as e:
                # Continue on error (encoding issues, parse errors, etc.)
                pass

        return functions

    def _should_index_file(self, file_path: Path) -> bool:
        """
        Check if file should be indexed (production code only)

        INCLUDES: Regular Go source files
        EXCLUDES: Tests, vendor, mocks, generated, configs
        """
        path_str = str(file_path)
        filename = file_path.name

        # SKIP: Test files
        if '_test.go' in filename:
            self.stats["skipped_tests"] += 1
            return False

        # SKIP: Vendor and mocks
        vendor_patterns = ['/vendor/', '/mocks/', '/mock_', '/testdata/']
        for pattern in vendor_patterns:
            if pattern in path_str:
                self.stats["skipped_vendor"] += 1
                return False

        # SKIP: Generated files
        generated_patterns = ['.pb.go', '.gen.go', 'generated']
        for pattern in generated_patterns:
            if pattern in filename.lower() or pattern in path_str.lower():
                self.stats["skipped_generated"] += 1
                return False

        # ONLY: .go files (this filters out YAML, JSON, etc.)
        if file_path.suffix != '.go':
            self.stats["skipped_other"] += 1
            return False

        return True

    def _index_file(self, file_path: Path, repo_path: Path) -> List[IndexedFunction]:
        """Index a single Go file"""
        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError):
            return []

        # Parse file
        functions = self.parser.parse_file(str(file_path), content)

        # Convert to IndexedFunction
        indexed = []
        repo_name = repo_path.name
        rel_path = file_path.relative_to(repo_path)

        for func in functions:
            indexed_func = self._create_indexed_function(func, repo_name, str(rel_path))
            indexed.append(indexed_func)

        return indexed

    def _create_indexed_function(self, func: GoFunction, repo_name: str, rel_path: str) -> IndexedFunction:
        """Convert GoFunction to IndexedFunction with metadata"""

        # Create unique ID
        func_id = f"{repo_name}/{rel_path}:{func.name}"

        # Create content for embedding
        # Include: docstring + signature + body (truncated to 500 chars)
        content_parts = []

        if func.docstring:
            content_parts.append(func.docstring)

        content_parts.append(func.signature)

        # Truncate body if too long
        body_preview = func.body[:500] if len(func.body) > 500 else func.body
        content_parts.append(body_preview)

        content = "\n".join(content_parts)

        # Detect code type from path
        code_type = self._detect_code_type(rel_path)

        # Create metadata (Chroma doesn't accept None values)
        metadata = {
            "repo": repo_name,
            "file": rel_path,
            "function": func.name,
            "start_line": func.start_line,
            "end_line": func.end_line,
            "lines_of_code": func.end_line - func.start_line + 1,
            "has_docstring": func.docstring is not None,
            "is_method": func.receiver is not None,
            "receiver": func.receiver if func.receiver else "",
            "code_type": code_type,
        }

        return IndexedFunction(
            id=func_id,
            content=content,
            metadata=metadata
        )

    def _detect_code_type(self, file_path: str) -> str:
        """Heuristically determine code type from file path"""
        path_lower = file_path.lower()

        if 'handler' in path_lower:
            return "handler"
        elif 'middleware' in path_lower:
            return "middleware"
        elif 'service' in path_lower:
            return "service"
        elif 'repository' in path_lower or 'repo.go' in path_lower:
            return "repository"
        elif 'model' in path_lower or 'entity' in path_lower:
            return "model"
        elif 'client' in path_lower:
            return "client"
        elif 'util' in path_lower or 'helper' in path_lower:
            return "utility"
        else:
            return "other"

    def _print_stats(self):
        """Print indexing statistics"""
        print(f"\n{'='*60}")
        print(f"📊 Indexing Statistics:")
        print(f"{'='*60}")
        print(f"  Total .go files found:     {self.stats['total_files']:>6}")
        print(f"  Skipped (tests):           {self.stats['skipped_tests']:>6}")
        print(f"  Skipped (vendor/mocks):    {self.stats['skipped_vendor']:>6}")
        print(f"  Skipped (generated):       {self.stats['skipped_generated']:>6}")
        print(f"  Indexed (production):      {self.stats['indexed_files']:>6}")
        print(f"  {'─'*60}")
        print(f"  Total functions extracted: {self.stats['total_functions']:>6}")
        print(f"{'='*60}\n")

    def save_index(self, functions: List[IndexedFunction], output_path: str):
        """Save indexed functions to JSON (for inspection/debugging)"""
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        data = [
            {
                "id": f.id,
                "content_preview": f.content[:150] + "..." if len(f.content) > 150 else f.content,
                "metadata": f.metadata
            }
            for f in functions
        ]

        with open(output, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"💾 Saved index preview to: {output}")


if __name__ == "__main__":
    # Test indexer
    import sys
    from dotenv import load_dotenv

    load_dotenv()

    repos_path = os.getenv("REPOS_PATH", "./repos")
    indexer = CodeIndexer(repos_path)

    functions = indexer.index_all_repos()

    # Show summary by repo
    repos_count = {}
    type_count = {}

    for func in functions:
        repo = func.metadata["repo"]
        code_type = func.metadata["code_type"]

        repos_count[repo] = repos_count.get(repo, 0) + 1
        type_count[code_type] = type_count.get(code_type, 0) + 1

    print("\n📊 Functions by repo:")
    for repo, count in sorted(repos_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {repo:30s}: {count:4d} functions")

    print("\n📊 Functions by type:")
    for code_type, count in sorted(type_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {code_type:15s}: {count:4d} functions")

    # Save preview
    indexer.save_index(functions[:100], "./data/index_preview.json")
    print(f"\n✅ Ready for embedding! ({len(functions)} functions)")
