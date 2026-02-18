"""
Indexer module - crawls repos, extracts functions from multiple languages,
detects patterns and frameworks, creates embeddings.
"""

from pathlib import Path
from typing import List, Dict, Set
from tqdm import tqdm
import json

from .models import CodeFunction, IndexedFunction
from .parsers.registry import ParserRegistry
from .detectors.pattern_detector import PatternDetector
from .detectors.framework_detector import FrameworkDetector

# Maximum lines before truncating embedding text (still store full code)
_MAX_EMBED_LINES = 500

# Per-language skip patterns
_SKIP_PATTERNS: Dict[str, Dict[str, list]] = {
    "go": {
        "file_suffixes": ["_test.go"],
        "path_contains": ["/vendor/", "/mocks/", "/mock_", "/testdata/"],
        "file_contains": [".pb.go", ".gen.go", "generated"],
    },
    "java": {
        "file_suffixes": ["Test.java", "Tests.java", "IT.java"],
        "path_contains": ["/src/test/", "/target/", "/build/", "/.gradle/", "/testdata/"],
        "file_contains": [],
    },
    "python": {
        "file_suffixes": ["_test.py"],
        "path_contains": ["/venv/", "/__pycache__/", "/migrations/", "/site-packages/",
                          "/.venv/", "/env/", "/.env/", "/test/", "/tests/"],
        "file_contains": [],
        "file_prefixes": ["test_"],
    },
    "javascript": {
        "file_suffixes": [".test.js", ".test.jsx", ".spec.js", ".spec.jsx",
                          ".test.mjs", ".spec.mjs", ".min.js"],
        "path_contains": ["/node_modules/", "/dist/", "/build/", "/.next/",
                          "/coverage/", "/__tests__/"],
        "file_contains": [],
    },
    "typescript": {
        "file_suffixes": [".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx",
                          ".d.ts"],
        "path_contains": ["/node_modules/", "/dist/", "/build/", "/.next/",
                          "/coverage/", "/__tests__/"],
        "file_contains": [],
    },
}


class CodeIndexer:
    """Crawls repositories and extracts functions from production code (multi-language)."""

    def __init__(self, repos_path: str):
        self.repos_path = Path(repos_path)
        self.registry = ParserRegistry()
        self.pattern_detector = PatternDetector()
        self.framework_detector = FrameworkDetector()
        self.stats: Dict[str, int] = {
            "total_files": 0,
            "skipped_tests": 0,
            "skipped_vendor": 0,
            "skipped_generated": 0,
            "skipped_other": 0,
            "indexed_files": 0,
            "total_functions": 0,
        }
        self.language_stats: Dict[str, int] = {}

    def index_all_repos(self) -> List[IndexedFunction]:
        """Index all production code in all repositories."""
        print(f"\n📂 Indexing production code from: {self.repos_path}")
        supported = ", ".join(sorted(self.registry.supported_extensions()))
        print(f"   Supported extensions: {supported}")
        print("   Excluding: tests, vendor, generated, build artifacts\n")

        all_functions: List[IndexedFunction] = []
        repos = [d for d in self.repos_path.iterdir() if d.is_dir() and not d.name.startswith('.')]

        for repo in repos:
            print(f"\n  📁 {repo.name}")
            repo_functions = self.index_repo(repo)
            all_functions.extend(repo_functions)
            print(f"     ✓ {len(repo_functions)} functions")

        self._print_stats()
        return all_functions

    def index_repo(self, repo_path: Path) -> List[IndexedFunction]:
        """Index all production files in a single repository."""
        functions: List[IndexedFunction] = []

        # Find all files with supported extensions
        supported_exts = self.registry.supported_extensions()
        source_files = []
        for ext in supported_exts:
            source_files.extend(repo_path.rglob(f"*{ext}"))

        self.stats["total_files"] += len(source_files)

        # Filter to production code
        production_files = [f for f in source_files if self._should_index_file(f)]
        self.stats["indexed_files"] += len(production_files)

        for src_file in tqdm(production_files, desc=f"  {repo_path.name}", leave=False):
            try:
                file_functions = self._index_file(src_file, repo_path)
                functions.extend(file_functions)
                self.stats["total_functions"] += len(file_functions)
            except Exception:
                pass

        return functions

    def _should_index_file(self, file_path: Path) -> bool:
        """Check if file should be indexed (production code only)."""
        ext = file_path.suffix
        language = self.registry.get_language(ext)
        if not language:
            self.stats["skipped_other"] += 1
            return False

        path_str = str(file_path)
        filename = file_path.name
        skip = _SKIP_PATTERNS.get(language, {})

        # Check file suffixes
        for suffix in skip.get("file_suffixes", []):
            if filename.endswith(suffix):
                self.stats["skipped_tests"] += 1
                return False

        # Check file prefixes (e.g., test_*)
        for prefix in skip.get("file_prefixes", []):
            if filename.startswith(prefix):
                self.stats["skipped_tests"] += 1
                return False

        # Check path contains
        for pattern in skip.get("path_contains", []):
            if pattern in path_str:
                self.stats["skipped_vendor"] += 1
                return False

        # Check file contains (generated files)
        for pattern in skip.get("file_contains", []):
            if pattern in filename.lower() or pattern in path_str.lower():
                self.stats["skipped_generated"] += 1
                return False

        return True

    def _index_file(self, file_path: Path, repo_path: Path) -> List[IndexedFunction]:
        """Index a single source file."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError):
            return []

        ext = file_path.suffix
        parser = self.registry.get_parser(ext)
        if not parser:
            return []

        language = self.registry.get_language(ext) or "unknown"

        # Parse file
        code_functions = parser.parse_file(str(file_path), content)

        # Detect file-level frameworks
        file_frameworks = self.framework_detector.detect_from_file(str(file_path), content)

        # Convert to IndexedFunction
        indexed: List[IndexedFunction] = []
        repo_name = repo_path.name
        rel_path = file_path.relative_to(repo_path)

        for func in code_functions:
            indexed_func = self._create_indexed_function(
                func, repo_name, str(rel_path), file_frameworks
            )
            indexed.append(indexed_func)

            # Track language stats
            self.language_stats[language] = self.language_stats.get(language, 0) + 1

        return indexed

    def _create_indexed_function(
        self,
        func: CodeFunction,
        repo_name: str,
        rel_path: str,
        file_frameworks: Set[str],
    ) -> IndexedFunction:
        """Convert CodeFunction to IndexedFunction with full metadata."""

        # Unique ID
        if func.class_name:
            func_id = f"{repo_name}/{rel_path}:{func.class_name}.{func.name}"
        else:
            func_id = f"{repo_name}/{rel_path}:{func.name}"

        # Detect patterns and frameworks
        patterns = self.pattern_detector.detect(func)
        frameworks = self.framework_detector.detect_from_function(func, file_frameworks)

        # Detect code type (enhanced: uses annotations/decorators + path)
        code_type = self._detect_code_type(func, rel_path)

        # Build embedding content: metadata prefix + decorators + docstring + full code
        embed_parts = []
        # Metadata prefix line
        prefix = f"[{func.language}] file:{rel_path}"
        if func.class_name:
            prefix += f" class:{func.class_name}"
        embed_parts.append(prefix)

        # Full code (truncate only for massive functions)
        code_lines = func.full_code.split('\n')
        if len(code_lines) > _MAX_EMBED_LINES:
            truncated_code = '\n'.join(code_lines[:_MAX_EMBED_LINES]) + '\n... (truncated)'
            embed_parts.append(truncated_code)
        else:
            embed_parts.append(func.full_code)

        content = "\n".join(embed_parts)

        # Metadata (Chroma doesn't accept None or list values)
        metadata = {
            "repo": repo_name,
            "file": rel_path,
            "function": func.name,
            "language": func.language,
            "start_line": func.start_line,
            "end_line": func.end_line,
            "lines_of_code": func.end_line - func.start_line + 1,
            "has_docstring": func.docstring is not None,
            "is_method": func.receiver is not None or func.class_name is not None,
            "receiver": func.receiver or "",
            "class_name": func.class_name or "",
            "construct_type": func.construct_type,
            "is_exported": func.is_exported,
            "code_type": code_type,
            "decorators": ",".join(func.decorators),
            "patterns": ",".join(patterns),
            "frameworks": ",".join(frameworks),
        }

        return IndexedFunction(
            id=func_id,
            content=content,
            full_code=func.full_code,
            metadata=metadata,
        )

    def _detect_code_type(self, func: CodeFunction, file_path: str) -> str:
        """Enhanced code type detection using annotations/decorators and file path."""
        decorators_str = " ".join(func.decorators).lower()
        path_lower = file_path.lower()

        # Annotation-based detection (highest priority)
        handler_annotations = ("@getmapping", "@postmapping", "@putmapping",
                               "@deletemapping", "@requestmapping",
                               "@app.route", "@router.get", "@router.post",
                               "@app.get", "@app.post")
        if any(a in decorators_str for a in handler_annotations):
            return "handler"

        middleware_annotations = ("@before", "@after", "@around",
                                 "@app.before_request", "@app.after_request")
        if any(a in decorators_str for a in middleware_annotations):
            return "middleware"

        service_annotations = ("@service",)
        if any(a in decorators_str for a in service_annotations):
            return "service"

        repo_annotations = ("@repository",)
        if any(a in decorators_str for a in repo_annotations):
            return "repository"

        # Name/path-based detection (fallback)
        if "handler" in path_lower or "controller" in path_lower:
            return "handler"
        elif "middleware" in path_lower:
            return "middleware"
        elif "service" in path_lower:
            return "service"
        elif "repository" in path_lower or "repo" in path_lower or "dao" in path_lower:
            return "repository"
        elif "model" in path_lower or "entity" in path_lower:
            return "model"
        elif "client" in path_lower:
            return "client"
        elif "util" in path_lower or "helper" in path_lower:
            return "utility"
        else:
            return "other"

    def _print_stats(self):
        """Print indexing statistics."""
        print(f"\n{'='*60}")
        print(f"📊 Indexing Statistics:")
        print(f"{'='*60}")
        print(f"  Total source files found:  {self.stats['total_files']:>6}")
        print(f"  Skipped (tests):           {self.stats['skipped_tests']:>6}")
        print(f"  Skipped (vendor/deps):     {self.stats['skipped_vendor']:>6}")
        print(f"  Skipped (generated):       {self.stats['skipped_generated']:>6}")
        print(f"  Indexed (production):      {self.stats['indexed_files']:>6}")
        print(f"  {'─'*56}")
        print(f"  Total functions extracted: {self.stats['total_functions']:>6}")

        if self.language_stats:
            print(f"\n  By language:")
            for lang, count in sorted(self.language_stats.items(), key=lambda x: x[1], reverse=True):
                print(f"    {lang:15s}: {count:6d}")

        print(f"{'='*60}\n")

    def save_index(self, functions: List[IndexedFunction], output_path: str):
        """Save indexed functions to JSON (for inspection/debugging)."""
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        data = [
            {
                "id": f.id,
                "content_preview": f.content[:150] + "..." if len(f.content) > 150 else f.content,
                "metadata": f.metadata,
            }
            for f in functions
        ]

        with open(output, 'w') as fh:
            json.dump(data, fh, indent=2)

        print(f"💾 Saved index preview to: {output}")
