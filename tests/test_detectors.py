"""Tests for src/detectors/ — pattern and framework detection."""

import pytest

from src.models import CodeFunction
from src.detectors.pattern_detector import PatternDetector
from src.detectors.framework_detector import FrameworkDetector


@pytest.fixture
def pattern_detector():
    return PatternDetector()


@pytest.fixture
def framework_detector():
    return FrameworkDetector()


def _make_func(**kwargs):
    """Helper to create a CodeFunction with sensible defaults."""
    defaults = dict(
        name="test",
        signature="func test()",
        body="{}",
        full_code="func test() {}",
        docstring=None,
        file_path="test.go",
        start_line=1,
        end_line=3,
        language="go",
    )
    defaults.update(kwargs)
    return CodeFunction(**defaults)


# ─── Pattern Detector ───────────────────────────────────────────

class TestPatternDetector:
    def test_factory_by_name_prefix(self, pattern_detector):
        func = _make_func(name="NewUserService")
        assert "factory" in pattern_detector.detect(func)

    def test_factory_by_create_prefix(self, pattern_detector):
        func = _make_func(name="CreateOrder", language="java")
        assert "factory" in pattern_detector.detect(func)

    def test_factory_by_class_name(self, pattern_detector):
        func = _make_func(name="build", class_name="UserFactory", language="java")
        assert "factory" in pattern_detector.detect(func)

    def test_singleton_get_instance(self, pattern_detector):
        func = _make_func(name="getInstance", language="java")
        assert "singleton" in pattern_detector.detect(func)

    def test_singleton_python_new(self, pattern_detector):
        func = _make_func(
            name="__new__",
            language="python",
            body="if cls._instance is None: cls._instance = super().__new__(cls)",
        )
        assert "singleton" in pattern_detector.detect(func)

    def test_singleton_go_sync_once(self, pattern_detector):
        func = _make_func(
            name="GetDB",
            language="go",
            body="once.Do(func() { db = connect() })\n// uses sync.Once",
        )
        assert "singleton" in pattern_detector.detect(func)

    def test_builder_with_prefix(self, pattern_detector):
        func = _make_func(
            name="WithTimeout",
            language="go",
            receiver="(b *Builder)",
            construct_type="method",
        )
        assert "builder" in pattern_detector.detect(func)

    def test_builder_class_name(self, pattern_detector):
        func = _make_func(name="setName", class_name="UserBuilder", language="java")
        assert "builder" in pattern_detector.detect(func)

    def test_strategy_interface(self, pattern_detector):
        func = _make_func(name="PaymentStrategy", construct_type="interface")
        assert "strategy" in pattern_detector.detect(func)

    def test_strategy_abstract_method(self, pattern_detector):
        func = _make_func(
            name="process",
            language="python",
            decorators=["@abstractmethod"],
        )
        assert "strategy" in pattern_detector.detect(func)

    def test_strategy_java_abstract(self, pattern_detector):
        func = _make_func(
            name="execute",
            language="java",
            modifiers=["public", "abstract"],
        )
        assert "strategy" in pattern_detector.detect(func)

    def test_decorator_go_handler_wrapping(self, pattern_detector):
        func = _make_func(
            name="LoggingMiddleware",
            signature="func LoggingMiddleware(next http.Handler) http.Handler",
            body="return http.HandlerFunc(func(w, r) { next.ServeHTTP(w, r) }) // wraps http.Handler",
        )
        assert "decorator" in pattern_detector.detect(func)

    def test_decorator_express_middleware(self, pattern_detector):
        func = _make_func(
            name="auth",
            language="javascript",
            signature="const auth = (req, res, next) =>",
        )
        assert "decorator" in pattern_detector.detect(func)

    def test_decorator_python_wrapper(self, pattern_detector):
        func = _make_func(
            name="require_auth",
            language="python",
            body="def wrapper(func): return decorated(func)",
        )
        assert "decorator" in pattern_detector.detect(func)

    def test_observer_by_name(self, pattern_detector):
        for name in ("Subscribe", "Publish", "Emit", "OnMessage", "addEventListener"):
            func = _make_func(name=name)
            assert "observer" in pattern_detector.detect(func), f"Expected observer for {name}"

    def test_observer_event_listener_annotation(self, pattern_detector):
        func = _make_func(
            name="handleEvent",
            language="java",
            decorators=["@EventListener"],
        )
        assert "observer" in pattern_detector.detect(func)

    def test_repository_crud_with_db_hints(self, pattern_detector):
        func = _make_func(
            name="FindByID",
            body='row := db.Query("SELECT * FROM users WHERE id = ?", id)',
        )
        assert "repository" in pattern_detector.detect(func)

    def test_repository_annotation(self, pattern_detector):
        func = _make_func(
            name="save",
            language="java",
            decorators=["@Repository"],
        )
        assert "repository" in pattern_detector.detect(func)

    def test_no_false_positive_on_plain_function(self, pattern_detector):
        func = _make_func(name="processData", body="return data.strip()")
        patterns = pattern_detector.detect(func)
        assert patterns == []


# ─── Framework Detector ─────────────────────────────────────────

class TestFrameworkDetector:
    # -- File-level imports --

    def test_spring_boot_imports(self, framework_detector):
        fw = framework_detector.detect_from_file(
            "App.java",
            'import org.springframework.boot.SpringApplication;',
        )
        assert "spring_boot" in fw

    def test_flask_imports(self, framework_detector):
        fw = framework_detector.detect_from_file("app.py", "from flask import Flask")
        assert "flask" in fw

    def test_express_imports(self, framework_detector):
        fw = framework_detector.detect_from_file(
            "server.js", 'const express = require("express");'
        )
        assert "express" in fw

    def test_react_imports(self, framework_detector):
        fw = framework_detector.detect_from_file(
            "App.tsx", "import React from 'react';"
        )
        assert "react" in fw

    def test_nestjs_imports(self, framework_detector):
        fw = framework_detector.detect_from_file(
            "app.ts", "import { Controller } from '@nestjs/common';"
        )
        assert "nestjs" in fw

    def test_angular_imports(self, framework_detector):
        fw = framework_detector.detect_from_file(
            "app.ts", "import { Component } from '@angular/core';"
        )
        assert "angular" in fw

    def test_file_level_cache(self, framework_detector):
        framework_detector.detect_from_file("a.py", "from flask import Flask")
        # Second call uses cache
        fw = framework_detector.detect_from_file("a.py", "GARBAGE CONTENT")
        assert "flask" in fw  # cached result, not re-parsed

    # -- Function-level annotations --

    def test_spring_annotations_on_java(self, framework_detector):
        func = _make_func(
            name="create",
            language="java",
            decorators=["@PostMapping(\"/users\")"],
        )
        fw = framework_detector.detect_from_function(func)
        assert "spring_mvc" in fw

    def test_flask_route_decorator(self, framework_detector):
        func = _make_func(
            name="login",
            language="python",
            decorators=['@app.route("/login")'],
        )
        fw = framework_detector.detect_from_function(func)
        assert "flask" in fw

    def test_nestjs_annotations_on_typescript(self, framework_detector):
        func = _make_func(
            name="findAll",
            language="typescript",
            decorators=["@Get()"],
        )
        fw = framework_detector.detect_from_function(func)
        assert "nestjs" in fw

    def test_express_middleware_signature(self, framework_detector):
        func = _make_func(
            name="auth",
            language="javascript",
            signature="const auth = (req, res, next) =>",
        )
        fw = framework_detector.detect_from_function(func)
        assert "express" in fw

    def test_express_middleware_typescript(self, framework_detector):
        func = _make_func(
            name="auth",
            language="typescript",
            signature="const auth = (req, res, next) =>",
        )
        fw = framework_detector.detect_from_function(func)
        assert "express" in fw

    # -- Body-level patterns --

    def test_react_hooks_in_body(self, framework_detector):
        func = _make_func(
            name="App",
            language="javascript",
            body="const [count, setCount] = useState(0);",
        )
        fw = framework_detector.detect_from_function(func)
        assert "react" in fw

    def test_nextjs_patterns_in_body(self, framework_detector):
        func = _make_func(
            name="getServerSideProps",
            language="javascript",
            body="return { props: await getServerSideProps() }",
        )
        fw = framework_detector.detect_from_function(func)
        assert "nextjs" in fw

    # -- Language-aware filtering (no cross-language false positives) --

    def test_spring_does_not_match_typescript(self, framework_detector):
        func = _make_func(
            name="UserController",
            language="typescript",
            decorators=["@Controller('users')"],
        )
        fw = framework_detector.detect_from_function(func)
        assert "spring_boot" not in fw

    def test_nestjs_does_not_match_java(self, framework_detector):
        func = _make_func(
            name="AppModule",
            language="java",
            decorators=["@Module({})"],
        )
        fw = framework_detector.detect_from_function(func)
        assert "nestjs" not in fw

    def test_flask_does_not_match_javascript(self, framework_detector):
        func = _make_func(
            name="route",
            language="javascript",
            decorators=["@app.route('/')"],
        )
        fw = framework_detector.detect_from_function(func)
        assert "flask" not in fw

    # -- File frameworks passed through --

    def test_file_frameworks_included_in_function_result(self, framework_detector):
        func = _make_func(name="handler", language="python")
        fw = framework_detector.detect_from_function(func, file_frameworks={"flask"})
        assert "flask" in fw
