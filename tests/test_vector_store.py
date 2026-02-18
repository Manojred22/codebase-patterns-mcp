"""Tests for src/vector_store.py — Chroma vector database wrapper."""

import tempfile

import pytest

from src.vector_store import VectorStore
from src.models import IndexedFunction


@pytest.fixture
def tmp_store():
    """Create a VectorStore in a temporary directory (no embedding generator)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = VectorStore(persist_directory=tmpdir)
        yield store


def _make_indexed(func_id, language="go", patterns="", frameworks=""):
    return IndexedFunction(
        id=func_id,
        content=f"[{language}] func {func_id}() {{}}",
        full_code=f"func {func_id}() {{}}",
        metadata={
            "repo": "test-repo",
            "file": "test.go",
            "function": func_id,
            "language": language,
            "start_line": 1,
            "end_line": 3,
            "lines_of_code": 3,
            "has_docstring": False,
            "is_method": False,
            "receiver": "",
            "class_name": "",
            "construct_type": "function",
            "is_exported": True,
            "code_type": "other",
            "decorators": "",
            "patterns": patterns,
            "frameworks": frameworks,
        },
    )


class TestVectorStoreInit:
    def test_init_without_embedding_generator(self, tmp_store):
        """VectorStore should initialize without an embedding generator."""
        assert tmp_store.embedding_generator is None
        assert tmp_store.collection.count() == 0

    def test_stats_on_empty_store(self, tmp_store):
        stats = tmp_store.get_stats()
        assert stats["total_functions"] == 0
        assert stats["repos"] == {}
        assert stats["languages"] == {}

    def test_search_without_generator_raises(self, tmp_store):
        with pytest.raises(RuntimeError, match="no embedding_generator"):
            tmp_store.search("test query")


class TestVectorStoreUpsert:
    def test_upsert_functions(self, tmp_store):
        funcs = [_make_indexed("func1"), _make_indexed("func2")]
        # Fake embeddings (dimension doesn't matter for storage-only test)
        embeddings = [[0.1] * 10, [0.2] * 10]

        tmp_store.add_functions(funcs, embeddings)
        assert tmp_store.collection.count() == 2

    def test_upsert_idempotent(self, tmp_store):
        """Running upsert twice with same IDs should not duplicate."""
        funcs = [_make_indexed("func1")]
        embeddings = [[0.1] * 10]

        tmp_store.add_functions(funcs, embeddings)
        tmp_store.add_functions(funcs, embeddings)
        assert tmp_store.collection.count() == 1

    def test_upsert_updates_data(self, tmp_store):
        func_v1 = _make_indexed("func1", language="go")
        func_v2 = _make_indexed("func1", language="python")
        embeddings = [[0.1] * 10]

        tmp_store.add_functions([func_v1], embeddings)
        tmp_store.add_functions([func_v2], embeddings)

        assert tmp_store.collection.count() == 1
        result = tmp_store.collection.get(ids=["func1"], include=["metadatas"])
        assert result["metadatas"][0]["language"] == "python"

    def test_none_embeddings_filtered(self, tmp_store):
        funcs = [_make_indexed("func1"), _make_indexed("func2")]
        embeddings = [[0.1] * 10, None]

        tmp_store.add_functions(funcs, embeddings)
        assert tmp_store.collection.count() == 1

    def test_stores_full_code_in_documents(self, tmp_store):
        func = _make_indexed("func1")
        func.full_code = "func func1() {\n    return 42\n}"
        embeddings = [[0.1] * 10]

        tmp_store.add_functions([func], embeddings)

        result = tmp_store.collection.get(ids=["func1"], include=["documents"])
        assert result["documents"][0] == "func func1() {\n    return 42\n}"


class TestVectorStoreStats:
    def test_stats_counts(self, tmp_store):
        funcs = [
            _make_indexed("f1", language="go", patterns="factory"),
            _make_indexed("f2", language="java", frameworks="spring_boot"),
            _make_indexed("f3", language="go", patterns="factory,singleton"),
        ]
        embeddings = [[0.1] * 10] * 3
        tmp_store.add_functions(funcs, embeddings)

        stats = tmp_store.get_stats()
        assert stats["total_functions"] == 3
        assert stats["languages"]["go"] == 2
        assert stats["languages"]["java"] == 1
        assert stats["patterns"]["factory"] == 2
        assert stats["patterns"]["singleton"] == 1
        assert stats["frameworks"]["spring_boot"] == 1

    def test_stats_does_not_load_documents(self, tmp_store):
        """get_stats should use include=['metadatas'] only."""
        funcs = [_make_indexed("f1")]
        embeddings = [[0.1] * 10]
        tmp_store.add_functions(funcs, embeddings)

        # This is a behavioral test — we verify it doesn't crash and returns data
        stats = tmp_store.get_stats()
        assert stats["total_functions"] == 1


class TestVectorStoreReset:
    def test_reset_clears_all_data(self, tmp_store):
        funcs = [_make_indexed("f1"), _make_indexed("f2")]
        embeddings = [[0.1] * 10] * 2
        tmp_store.add_functions(funcs, embeddings)
        assert tmp_store.collection.count() == 2

        tmp_store.reset()
        assert tmp_store.collection.count() == 0
