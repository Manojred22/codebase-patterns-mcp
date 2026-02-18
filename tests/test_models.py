"""Tests for src/models.py — unified data models."""

from src.models import CodeFunction, GoFunction, IndexedFunction


def test_code_function_defaults():
    func = CodeFunction(
        name="foo",
        signature="func foo()",
        body="{ return 1 }",
        full_code="func foo() { return 1 }",
        docstring=None,
        file_path="test.go",
        start_line=1,
        end_line=3,
        language="go",
    )
    assert func.receiver is None
    assert func.class_name is None
    assert func.decorators == []
    assert func.modifiers == []
    assert func.is_exported is True
    assert func.construct_type == "function"


def test_go_function_alias():
    """GoFunction should be an alias for CodeFunction."""
    assert GoFunction is CodeFunction


def test_indexed_function_has_full_code():
    idx = IndexedFunction(
        id="repo/file.go:Foo",
        content="[go] file:file.go\nfunc Foo() {}",
        full_code="func Foo() {\n    return bar()\n}",
        metadata={"language": "go"},
    )
    assert idx.full_code == "func Foo() {\n    return bar()\n}"
    assert idx.content.startswith("[go]")
