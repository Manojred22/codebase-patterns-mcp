"""Tests for src/indexer.py — multi-language code indexing pipeline."""

import tempfile
from pathlib import Path

import pytest

from src.indexer import CodeIndexer


@pytest.fixture
def sample_repo():
    """Create a temp directory with sample files in all supported languages."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir) / "sample-repo"
        repo.mkdir()

        # Go
        (repo / "handler.go").write_text(
            'package main\n\n'
            '// CreateUser handles user creation\n'
            'func CreateUser(w http.ResponseWriter, r *http.Request) {\n'
            '    user := NewUser(r)\n'
            '}\n'
        )

        # Java
        src_main = repo / "src" / "main"
        src_main.mkdir(parents=True)
        (src_main / "UserService.java").write_text(
            'import org.springframework.stereotype.Service;\n\n'
            '@Service\n'
            'public class UserService {\n'
            '    public User findById(Long id) {\n'
            '        return repository.findById(id);\n'
            '    }\n'
            '}\n'
        )

        # Python
        (repo / "app.py").write_text(
            'from flask import Flask\n\n'
            'app = Flask(__name__)\n\n'
            '@app.route("/users")\n'
            'def list_users():\n'
            '    """List all users."""\n'
            '    return get_all_users()\n'
        )

        # JavaScript
        (repo / "server.js").write_text(
            'const express = require("express");\n\n'
            'const auth = (req, res, next) => {\n'
            '    next();\n'
            '};\n'
        )

        # TypeScript
        (repo / "api.controller.ts").write_text(
            'import { Controller, Get } from "@nestjs/common";\n\n'
            '@Controller("api")\n'
            'export class ApiController {\n'
            '    @Get()\n'
            '    async getAll() { return []; }\n'
            '}\n'
        )

        # TSX
        (repo / "Button.tsx").write_text(
            'import React from "react";\n\n'
            'export const Button = ({ label }: { label: string }) => {\n'
            '    return <button>{label}</button>;\n'
            '};\n'
        )

        # --- Files that should be SKIPPED ---
        (repo / "handler_test.go").write_text(
            "package main\nfunc TestHandler(t *testing.T) {}\n"
        )
        src_test = repo / "src" / "test"
        src_test.mkdir(parents=True)
        (src_test / "UserServiceTest.java").write_text("class Test {}\n")
        (repo / "test_app.py").write_text("def test_something(): pass\n")
        (repo / "server.test.js").write_text('test("auth", () => {});\n')
        (repo / "api.spec.ts").write_text('describe("api", () => {});\n')
        (repo / "types.d.ts").write_text('declare module "lib" {}\n')

        yield tmpdir


class TestIndexerMultiLanguage:
    def test_indexes_all_languages(self, sample_repo):
        indexer = CodeIndexer(sample_repo)
        functions = indexer.index_all_repos()

        languages = {f.metadata["language"] for f in functions}
        assert "go" in languages
        assert "java" in languages
        assert "python" in languages
        assert "javascript" in languages
        assert "typescript" in languages

    def test_skips_test_files(self, sample_repo):
        indexer = CodeIndexer(sample_repo)
        functions = indexer.index_all_repos()

        files = {f.metadata["file"] for f in functions}
        for f in files:
            assert "_test.go" not in f
            assert "Test.java" not in f
            assert not f.startswith("test_")
            assert ".test.js" not in f
            assert ".spec.ts" not in f
            assert ".d.ts" not in f

    def test_skips_java_test_directory(self, sample_repo):
        indexer = CodeIndexer(sample_repo)
        functions = indexer.index_all_repos()

        files = {f.metadata["file"] for f in functions}
        for f in files:
            assert "/src/test/" not in f

    def test_skip_stats_tracked(self, sample_repo):
        indexer = CodeIndexer(sample_repo)
        indexer.index_all_repos()
        assert indexer.stats["skipped_tests"] > 0

    def test_language_stats_tracked(self, sample_repo):
        indexer = CodeIndexer(sample_repo)
        indexer.index_all_repos()
        assert len(indexer.language_stats) >= 5


class TestIndexedFunctionContent:
    def test_full_code_stored(self, sample_repo):
        indexer = CodeIndexer(sample_repo)
        functions = indexer.index_all_repos()

        for f in functions:
            assert f.full_code, f"Missing full_code for {f.id}"
            assert len(f.full_code) > 5

    def test_embedding_content_has_language_prefix(self, sample_repo):
        indexer = CodeIndexer(sample_repo)
        functions = indexer.index_all_repos()

        for f in functions:
            lang = f.metadata["language"]
            assert f.content.startswith(f"[{lang}]"), (
                f"Expected [{lang}] prefix in content for {f.id}, got: {f.content[:40]}"
            )

    def test_metadata_has_required_fields(self, sample_repo):
        indexer = CodeIndexer(sample_repo)
        functions = indexer.index_all_repos()

        required_keys = {
            "repo", "file", "function", "language", "start_line", "end_line",
            "lines_of_code", "has_docstring", "is_method", "code_type",
            "construct_type", "patterns", "frameworks",
        }
        for f in functions:
            missing = required_keys - set(f.metadata.keys())
            assert not missing, f"Missing metadata keys for {f.id}: {missing}"

    def test_unique_ids(self, sample_repo):
        indexer = CodeIndexer(sample_repo)
        functions = indexer.index_all_repos()

        ids = [f.id for f in functions]
        assert len(ids) == len(set(ids)), "Duplicate IDs found"


class TestPatternAndFrameworkIntegration:
    def test_detects_patterns(self, sample_repo):
        indexer = CodeIndexer(sample_repo)
        functions = indexer.index_all_repos()

        all_patterns = set()
        for f in functions:
            for p in f.metadata["patterns"].split(","):
                if p.strip():
                    all_patterns.add(p.strip())

        # At least some patterns should be detected from sample code
        assert len(all_patterns) > 0

    def test_detects_frameworks(self, sample_repo):
        indexer = CodeIndexer(sample_repo)
        functions = indexer.index_all_repos()

        all_frameworks = set()
        for f in functions:
            for fw in f.metadata["frameworks"].split(","):
                if fw.strip():
                    all_frameworks.add(fw.strip())

        assert "spring_boot" in all_frameworks
        assert "flask" in all_frameworks
        assert "express" in all_frameworks
        assert "nestjs" in all_frameworks

    def test_code_type_detection(self, sample_repo):
        indexer = CodeIndexer(sample_repo)
        functions = indexer.index_all_repos()

        types = {f.metadata["code_type"] for f in functions}
        # handler.go should produce handler type, app.py with @app.route should too
        assert "handler" in types


class TestCodeTypeDetection:
    def test_annotation_based_handler(self):
        """@GetMapping should produce handler code_type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "repo"
            repo.mkdir()
            (repo / "Ctrl.java").write_text(
                '@GetMapping("/foo")\n'
                'public String foo() { return "bar"; }\n'
            )
            indexer = CodeIndexer(tmpdir)
            functions = indexer.index_all_repos()

            foo = next((f for f in functions if f.metadata["function"] == "foo"), None)
            assert foo is not None
            assert foo.metadata["code_type"] == "handler"

    def test_path_based_service(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "repo"
            (repo / "service").mkdir(parents=True)
            (repo / "service" / "auth.py").write_text(
                "def authenticate(user):\n    return True\n"
            )
            indexer = CodeIndexer(tmpdir)
            functions = indexer.index_all_repos()

            auth = next((f for f in functions if f.metadata["function"] == "authenticate"), None)
            assert auth is not None
            assert auth.metadata["code_type"] == "service"
