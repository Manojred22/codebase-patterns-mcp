"""
AST-based design pattern detection.
Operates on CodeFunction metadata — no re-parsing needed.
"""

import re
from typing import List

from ..models import CodeFunction


class PatternDetector:
    """Detect design patterns from CodeFunction metadata."""

    def detect(self, func: CodeFunction) -> List[str]:
        """Return list of detected pattern names for a function."""
        patterns = []

        if self._is_factory(func):
            patterns.append("factory")
        if self._is_singleton(func):
            patterns.append("singleton")
        if self._is_builder(func):
            patterns.append("builder")
        if self._is_strategy(func):
            patterns.append("strategy")
        if self._is_decorator(func):
            patterns.append("decorator")
        if self._is_observer(func):
            patterns.append("observer")
        if self._is_repository(func):
            patterns.append("repository")

        return patterns

    def _is_factory(self, func: CodeFunction) -> bool:
        name = func.name
        # Go: NewFoo, CreateBar; Java/Python: buildFoo, makeFoo, of, from
        factory_prefixes = ("New", "Create", "build", "make", "create", "new")
        factory_names = ("of", "from", "valueOf", "newInstance")
        if any(name.startswith(p) for p in factory_prefixes):
            return True
        if name in factory_names:
            return True
        # Class name contains Factory
        if func.class_name and "Factory" in func.class_name:
            return True
        if "Factory" in name:
            return True
        return False

    def _is_singleton(self, func: CodeFunction) -> bool:
        name = func.name
        if name in ("getInstance", "GetInstance", "get_instance", "instance"):
            return True
        # Python __new__ with _instance pattern
        if name == "__new__" and "_instance" in func.body:
            return True
        # Go sync.Once usage
        if func.language == "go" and "sync.Once" in func.body:
            return True
        return False

    def _is_builder(self, func: CodeFunction) -> bool:
        name = func.name
        # Builder methods: With*, Set*
        if name.startswith("With") or name.startswith("Set") or name.startswith("set"):
            # Check if returns self/this/receiver
            body = func.body
            if "return self" in body or "return this" in body:
                return True
            # Go: returns receiver type
            if func.receiver and func.language == "go":
                return True
        # Class name contains Builder
        if func.class_name and "Builder" in func.class_name:
            return True
        if "Builder" in name:
            return True
        # build() / Build() method
        if name in ("build", "Build"):
            return True
        return False

    def _is_strategy(self, func: CodeFunction) -> bool:
        # Interface declaration
        if func.construct_type == "interface":
            return True
        # Python ABC / Protocol
        if func.language == "python":
            decorators_str = " ".join(func.decorators)
            if "@abstractmethod" in decorators_str:
                return True
            if func.construct_type == "class":
                if "ABC" in func.signature or "Protocol" in func.signature:
                    return True
        # Java abstract class
        if func.language == "java" and "abstract" in func.modifiers:
            return True
        return False

    def _is_decorator(self, func: CodeFunction) -> bool:
        name = func.name
        body = func.body
        # Go: handler wrapping (accepts and returns http.Handler)
        if func.language == "go":
            if "http.Handler" in func.signature and "http.Handler" in body:
                return True
        # Java AOP annotations
        aop_annotations = ("@Around", "@Before", "@After", "@Aspect")
        if any(a in " ".join(func.decorators) for a in aop_annotations):
            return True
        # Express middleware: (req, res, next) pattern
        if func.language == "javascript":
            if re.search(r"\(req\s*,\s*res\s*,\s*next\)", func.signature):
                return True
        # Python decorator pattern: function that returns a function
        if func.language == "python":
            if "def wrapper" in body or "def inner" in body or "def decorated" in body:
                return True
        return False

    def _is_observer(self, func: CodeFunction) -> bool:
        name = func.name
        observer_words = ("Subscribe", "Publish", "Emit", "Listen",
                          "subscribe", "publish", "emit", "listen",
                          "AddListener", "RemoveListener",
                          "addEventListener", "removeEventListener")
        if any(w in name for w in observer_words):
            return True
        # On + capitalized (e.g., OnMessage, OnConnect)
        if re.match(r"^[Oo]n[A-Z]", name):
            return True
        # Java @EventListener
        if "@EventListener" in " ".join(func.decorators):
            return True
        # Go channel operations
        if func.language == "go" and ("<-" in func.body):
            # Check for channel pattern (send/receive in a loop or select)
            if "select" in func.body or "for" in func.body:
                return True
        return False

    def _is_repository(self, func: CodeFunction) -> bool:
        name = func.name
        crud_words = ("Find", "Get", "Save", "Create", "Update", "Delete",
                      "List", "Insert", "Remove", "Fetch", "Store",
                      "find", "get", "save", "create", "update", "delete",
                      "list", "insert", "remove", "fetch", "store")
        # Name starts with a CRUD word
        if any(name.startswith(w) for w in crud_words):
            # Additional heuristic: body should reference DB-like operations
            body = func.body.lower()
            db_hints = ("query", "exec", "cursor", "session", "transaction",
                        "sql", "select", "insert", "update", "delete",
                        "collection", "table", "repository", "dao", "db.",
                        "database", ".find(", ".save(", ".delete(",
                        "entitymanager", "jdbctemplate")
            if any(h in body for h in db_hints):
                return True
        # Java @Repository annotation
        if "@Repository" in " ".join(func.decorators):
            return True
        # Class extends JPA/CrudRepository
        if func.class_name and any(r in (func.class_name or "") for r in ("Repository",)):
            if func.language == "java":
                return True
        return False
