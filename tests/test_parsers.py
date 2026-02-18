"""Tests for src/parsers/ — multi-language tree-sitter parsers."""

import pytest

from src.parsers.registry import ParserRegistry, EXTENSION_MAP


@pytest.fixture
def registry():
    return ParserRegistry()


# ─── Registry ───────────────────────────────────────────────────

class TestParserRegistry:
    def test_extension_mapping(self, registry):
        assert registry.get_language(".go") == "go"
        assert registry.get_language(".java") == "java"
        assert registry.get_language(".py") == "python"
        assert registry.get_language(".js") == "javascript"
        assert registry.get_language(".jsx") == "javascript"
        assert registry.get_language(".mjs") == "javascript"
        assert registry.get_language(".ts") == "typescript"
        assert registry.get_language(".tsx") == "typescript"

    def test_unsupported_extension_returns_none(self, registry):
        assert registry.get_language(".rs") is None
        assert registry.get_parser(".rs") is None

    def test_supported_extensions(self, registry):
        exts = registry.supported_extensions()
        assert ".go" in exts
        assert ".java" in exts
        assert ".py" in exts
        assert ".js" in exts
        assert ".ts" in exts
        assert ".tsx" in exts

    def test_lazy_parser_instantiation(self, registry):
        assert len(registry._parsers) == 0
        registry.get_parser(".go")
        assert "go" in registry._parsers
        assert len(registry._parsers) == 1


# ─── Go Parser ──────────────────────────────────────────────────

class TestGoParser:
    GO_CODE = '''\
package main

// Add adds two numbers
func Add(a, b int) int {
    return a + b
}

type Service struct{}

func (s *Service) Handle(w http.ResponseWriter, r *http.Request) {
    w.Write([]byte("ok"))
}

func privateHelper() {}
'''

    def test_extracts_functions_and_methods(self, registry):
        parser = registry.get_parser(".go")
        funcs = parser.parse_file("test.go", self.GO_CODE)
        assert len(funcs) == 3
        names = [f.name for f in funcs]
        assert "Add" in names
        assert "Handle" in names
        assert "privateHelper" in names

    def test_function_metadata(self, registry):
        parser = registry.get_parser(".go")
        funcs = parser.parse_file("test.go", self.GO_CODE)
        add_func = next(f for f in funcs if f.name == "Add")

        assert add_func.language == "go"
        assert add_func.construct_type == "function"
        assert add_func.is_exported is True
        assert add_func.receiver is None
        assert add_func.docstring is not None
        assert "adds two numbers" in add_func.docstring

    def test_method_has_receiver(self, registry):
        parser = registry.get_parser(".go")
        funcs = parser.parse_file("test.go", self.GO_CODE)
        handle = next(f for f in funcs if f.name == "Handle")

        assert handle.construct_type == "method"
        assert handle.receiver is not None
        assert "Service" in handle.receiver

    def test_unexported_function(self, registry):
        parser = registry.get_parser(".go")
        funcs = parser.parse_file("test.go", self.GO_CODE)
        helper = next(f for f in funcs if f.name == "privateHelper")
        assert helper.is_exported is False

    def test_full_code_not_truncated(self, registry):
        parser = registry.get_parser(".go")
        funcs = parser.parse_file("test.go", self.GO_CODE)
        for f in funcs:
            assert len(f.full_code) > 0
            assert f.name in f.full_code


# ─── Java Parser ────────────────────────────────────────────────

class TestJavaParser:
    JAVA_CODE = '''\
package com.example;

import org.springframework.web.bind.annotation.*;

@RestController
public class UserController {

    /** Create a new user */
    @PostMapping("/users")
    public User createUser(@RequestBody UserRequest request) {
        return userService.create(request);
    }

    @GetMapping("/users/{id}")
    public User getUser(@PathVariable Long id) {
        return userService.findById(id);
    }
}
'''

    def test_extracts_class_and_methods(self, registry):
        parser = registry.get_parser(".java")
        funcs = parser.parse_file("UserController.java", self.JAVA_CODE)
        names = [f.name for f in funcs]
        assert "UserController" in names
        assert "createUser" in names
        assert "getUser" in names

    def test_class_annotations(self, registry):
        parser = registry.get_parser(".java")
        funcs = parser.parse_file("UserController.java", self.JAVA_CODE)
        cls = next(f for f in funcs if f.name == "UserController")

        assert cls.construct_type == "class"
        assert cls.language == "java"
        assert "@RestController" in cls.decorators

    def test_method_annotations_and_class_name(self, registry):
        parser = registry.get_parser(".java")
        funcs = parser.parse_file("UserController.java", self.JAVA_CODE)
        create = next(f for f in funcs if f.name == "createUser")

        assert create.construct_type == "method"
        assert create.class_name == "UserController"
        assert any("@PostMapping" in a for a in create.decorators)

    def test_no_annotation_duplication_in_full_code(self, registry):
        parser = registry.get_parser(".java")
        code = '''\
@Service
public class Svc {
    public void doWork() {}
}
'''
        funcs = parser.parse_file("Svc.java", code)
        cls = next(f for f in funcs if f.name == "Svc")
        # @Service should appear exactly once in full_code
        assert cls.full_code.count("@Service") == 1

    def test_modifiers_extracted(self, registry):
        parser = registry.get_parser(".java")
        funcs = parser.parse_file("UserController.java", self.JAVA_CODE)
        cls = next(f for f in funcs if f.name == "UserController")
        assert "public" in cls.modifiers

    def test_javadoc_extraction(self, registry):
        parser = registry.get_parser(".java")
        funcs = parser.parse_file("UserController.java", self.JAVA_CODE)
        create = next(f for f in funcs if f.name == "createUser")
        assert create.docstring is not None
        assert "Create a new user" in create.docstring

    def test_interface_extraction(self, registry):
        parser = registry.get_parser(".java")
        code = '''\
public interface UserRepository {
    User findById(Long id);
}
'''
        funcs = parser.parse_file("UserRepository.java", code)
        iface = next((f for f in funcs if f.name == "UserRepository"), None)
        assert iface is not None
        assert iface.construct_type == "interface"

    def test_constructor_extraction(self, registry):
        parser = registry.get_parser(".java")
        code = '''\
public class Foo {
    public Foo(int x) {
        this.x = x;
    }
}
'''
        funcs = parser.parse_file("Foo.java", code)
        ctor = next((f for f in funcs if f.construct_type == "constructor"), None)
        assert ctor is not None
        assert ctor.name == "Foo"


# ─── Python Parser ──────────────────────────────────────────────

class TestPythonParser:
    PYTHON_CODE = '''\
from flask import Flask, request

app = Flask(__name__)

def helper_function():
    """A simple helper."""
    return 42

class AuthService:
    @staticmethod
    def validate_token(token: str) -> bool:
        """Validates JWT tokens."""
        return verify(token)

    def _internal_method(self):
        pass

@app.route("/login", methods=["POST"])
def login():
    """Handle login requests."""
    data = request.json
    return authenticate(data)
'''

    def test_extracts_all_constructs(self, registry):
        parser = registry.get_parser(".py")
        funcs = parser.parse_file("app.py", self.PYTHON_CODE)
        names = [f.name for f in funcs]
        assert "helper_function" in names
        assert "AuthService" in names
        assert "validate_token" in names
        assert "_internal_method" in names
        assert "login" in names

    def test_function_language(self, registry):
        parser = registry.get_parser(".py")
        funcs = parser.parse_file("app.py", self.PYTHON_CODE)
        for f in funcs:
            assert f.language == "python"

    def test_class_construct_type(self, registry):
        parser = registry.get_parser(".py")
        funcs = parser.parse_file("app.py", self.PYTHON_CODE)
        cls = next(f for f in funcs if f.name == "AuthService")
        assert cls.construct_type == "class"

    def test_method_has_class_name(self, registry):
        parser = registry.get_parser(".py")
        funcs = parser.parse_file("app.py", self.PYTHON_CODE)
        validate = next(f for f in funcs if f.name == "validate_token")
        assert validate.class_name == "AuthService"
        assert validate.construct_type == "method"

    def test_decorated_function(self, registry):
        parser = registry.get_parser(".py")
        funcs = parser.parse_file("app.py", self.PYTHON_CODE)
        login = next(f for f in funcs if f.name == "login")
        assert any("@app.route" in d for d in login.decorators)

    def test_decorator_on_method(self, registry):
        parser = registry.get_parser(".py")
        funcs = parser.parse_file("app.py", self.PYTHON_CODE)
        validate = next(f for f in funcs if f.name == "validate_token")
        assert "@staticmethod" in validate.decorators

    def test_private_method_not_exported(self, registry):
        parser = registry.get_parser(".py")
        funcs = parser.parse_file("app.py", self.PYTHON_CODE)
        internal = next(f for f in funcs if f.name == "_internal_method")
        assert internal.is_exported is False

    def test_docstring_extraction(self, registry):
        parser = registry.get_parser(".py")
        funcs = parser.parse_file("app.py", self.PYTHON_CODE)
        helper = next(f for f in funcs if f.name == "helper_function")
        assert helper.docstring is not None
        assert "simple helper" in helper.docstring


# ─── JavaScript Parser ──────────────────────────────────────────

class TestJavaScriptParser:
    JS_CODE = '''\
const express = require("express");

function processData(input) {
    return input.trim();
}

const handleRequest = (req, res, next) => {
    res.json({ ok: true });
};

class UserService {
    constructor(db) {
        this.db = db;
    }

    async findById(id) {
        return this.db.query("SELECT * FROM users WHERE id = ?", [id]);
    }
}

export default UserService;
'''

    def test_extracts_all_constructs(self, registry):
        parser = registry.get_parser(".js")
        funcs = parser.parse_file("server.js", self.JS_CODE)
        names = [f.name for f in funcs]
        assert "processData" in names
        assert "handleRequest" in names
        assert "UserService" in names
        assert "constructor" in names
        assert "findById" in names

    def test_function_language(self, registry):
        parser = registry.get_parser(".js")
        funcs = parser.parse_file("server.js", self.JS_CODE)
        for f in funcs:
            assert f.language == "javascript"

    def test_arrow_function_extracted(self, registry):
        parser = registry.get_parser(".js")
        funcs = parser.parse_file("server.js", self.JS_CODE)
        handler = next(f for f in funcs if f.name == "handleRequest")
        assert handler.construct_type == "function"

    def test_class_construct_type(self, registry):
        parser = registry.get_parser(".js")
        funcs = parser.parse_file("server.js", self.JS_CODE)
        cls = next(f for f in funcs if f.name == "UserService")
        assert cls.construct_type == "class"

    def test_constructor_detected(self, registry):
        parser = registry.get_parser(".js")
        funcs = parser.parse_file("server.js", self.JS_CODE)
        ctor = next(f for f in funcs if f.name == "constructor")
        assert ctor.construct_type == "constructor"
        assert ctor.class_name == "UserService"

    def test_method_has_class_name(self, registry):
        parser = registry.get_parser(".js")
        funcs = parser.parse_file("server.js", self.JS_CODE)
        find = next(f for f in funcs if f.name == "findById")
        assert find.class_name == "UserService"
        assert find.construct_type == "method"


# ─── TypeScript Parser ──────────────────────────────────────────

class TestTypeScriptParser:
    TS_CODE = '''\
import { Injectable } from "@nestjs/common";
import { Repository } from "typeorm";

interface UserDTO {
    id: number;
    name: string;
    email: string;
}

@Injectable()
export class UserService {
    constructor(private readonly userRepo: Repository<User>) {}

    async findById(id: number): Promise<User | null> {
        return this.userRepo.findOne({ where: { id } });
    }

    async createUser(dto: UserDTO): Promise<User> {
        const user = this.userRepo.create(dto);
        return this.userRepo.save(user);
    }
}

export function formatUser(user: User): string {
    return JSON.stringify(user);
}

export const fetchUsers = async (limit: number): Promise<User[]> => {
    const response = await fetch("/api/users?limit=" + limit);
    return response.json();
};
'''

    def test_extracts_all_constructs(self, registry):
        parser = registry.get_parser(".ts")
        funcs = parser.parse_file("user.service.ts", self.TS_CODE)
        names = [f.name for f in funcs]
        assert "UserDTO" in names
        assert "UserService" in names
        assert "constructor" in names
        assert "findById" in names
        assert "createUser" in names
        assert "formatUser" in names
        assert "fetchUsers" in names

    def test_language_is_typescript(self, registry):
        parser = registry.get_parser(".ts")
        funcs = parser.parse_file("user.service.ts", self.TS_CODE)
        for f in funcs:
            assert f.language == "typescript"

    def test_interface_extraction(self, registry):
        parser = registry.get_parser(".ts")
        funcs = parser.parse_file("user.service.ts", self.TS_CODE)
        dto = next(f for f in funcs if f.name == "UserDTO")
        assert dto.construct_type == "interface"

    def test_class_decorators(self, registry):
        parser = registry.get_parser(".ts")
        funcs = parser.parse_file("user.service.ts", self.TS_CODE)
        svc = next(f for f in funcs if f.name == "UserService")
        assert svc.construct_type == "class"
        assert svc.is_exported is True
        assert any("@Injectable" in d for d in svc.decorators)

    def test_method_class_name(self, registry):
        parser = registry.get_parser(".ts")
        funcs = parser.parse_file("user.service.ts", self.TS_CODE)
        find = next(f for f in funcs if f.name == "findById")
        assert find.class_name == "UserService"
        assert find.construct_type == "method"

    def test_exported_function(self, registry):
        parser = registry.get_parser(".ts")
        funcs = parser.parse_file("user.service.ts", self.TS_CODE)
        fmt = next(f for f in funcs if f.name == "formatUser")
        assert fmt.is_exported is True
        assert fmt.construct_type == "function"

    def test_arrow_function(self, registry):
        parser = registry.get_parser(".ts")
        funcs = parser.parse_file("user.service.ts", self.TS_CODE)
        fetch = next(f for f in funcs if f.name == "fetchUsers")
        assert fetch.is_exported is True
        assert fetch.construct_type == "function"


class TestTSXParser:
    TSX_CODE = '''\
import React, { useState } from "react";

interface Props {
    title: string;
}

const App: React.FC<Props> = ({ title }) => {
    const [count, setCount] = useState(0);
    return (
        <div>
            <h1>{title}</h1>
            <button onClick={() => setCount(count + 1)}>Count: {count}</button>
        </div>
    );
};

export default App;
'''

    def test_tsx_uses_typescript_language(self, registry):
        assert registry.get_language(".tsx") == "typescript"

    def test_tsx_extracts_interface(self, registry):
        parser = registry.get_parser(".tsx")
        funcs = parser.parse_file("App.tsx", self.TSX_CODE)
        props = next((f for f in funcs if f.name == "Props"), None)
        assert props is not None
        assert props.construct_type == "interface"
        assert props.language == "typescript"

    def test_tsx_extracts_component(self, registry):
        parser = registry.get_parser(".tsx")
        funcs = parser.parse_file("App.tsx", self.TSX_CODE)
        app = next((f for f in funcs if f.name == "App"), None)
        assert app is not None
        assert app.language == "typescript"
