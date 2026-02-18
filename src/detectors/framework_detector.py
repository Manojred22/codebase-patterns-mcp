"""
Framework detection from annotations, decorators, and imports.
Two levels: file-level (imports, cached) and function-level (annotations/decorators).
"""

import re
from typing import Dict, List, Set

from ..models import CodeFunction


# File-level import patterns → framework
_IMPORT_PATTERNS: Dict[str, List[str]] = {
    # Java
    "spring_boot": [
        "org.springframework.boot",
        "org.springframework.web",
        "org.springframework.stereotype",
        "org.springframework.beans",
    ],
    "spring_mvc": [
        "org.springframework.web.bind.annotation",
    ],
    "jpa": [
        "javax.persistence",
        "jakarta.persistence",
        "org.springframework.data.jpa",
    ],
    "lombok": [
        "lombok.",
    ],
    # Python
    "flask": [
        "from flask",
        "import flask",
    ],
    "django": [
        "from django",
        "import django",
    ],
    "fastapi": [
        "from fastapi",
        "import fastapi",
    ],
    "sqlalchemy": [
        "from sqlalchemy",
        "import sqlalchemy",
    ],
    "celery": [
        "from celery",
        "import celery",
    ],
    # JavaScript
    "express": [
        "require('express')",
        'require("express")',
        "from 'express'",
        'from "express"',
    ],
    "react": [
        "require('react')",
        'require("react")',
        "from 'react'",
        'from "react"',
    ],
    "nextjs": [
        "from 'next",
        'from "next',
        "require('next",
        'require("next',
    ],
    # TypeScript-specific
    "nestjs": [
        "from '@nestjs/",
        "'@nestjs/common'",
        "'@nestjs/core'",
    ],
    "angular": [
        "from '@angular/",
        "'@angular/core'",
        "'@angular/common'",
    ],
    "typeorm": [
        "from 'typeorm'",
        'from "typeorm"',
    ],
    "prisma": [
        "from '@prisma/",
        "'@prisma/client'",
    ],
}

# Function-level annotation/decorator patterns → framework
_ANNOTATION_PATTERNS: Dict[str, List[str]] = {
    # Java Spring
    "spring_boot": [
        "@RestController", "@Controller", "@Service", "@Repository",
        "@Configuration", "@Autowired", "@Component", "@Bean",
        "@SpringBootApplication",
    ],
    "spring_mvc": [
        "@GetMapping", "@PostMapping", "@PutMapping", "@DeleteMapping",
        "@PatchMapping", "@RequestMapping", "@PathVariable", "@RequestBody",
        "@RequestParam", "@ResponseBody",
    ],
    "jpa": [
        "@Entity", "@Table", "@Column", "@Id", "@GeneratedValue",
        "@OneToMany", "@ManyToOne", "@ManyToMany", "@OneToOne",
        "@JoinColumn", "@Transactional",
    ],
    "lombok": [
        "@Data", "@Builder", "@Getter", "@Setter", "@NoArgsConstructor",
        "@AllArgsConstructor", "@Value", "@Slf4j", "@Log",
    ],
    # Python
    "flask": [
        "@app.route", "@blueprint.route", "@app.before_request",
        "@app.after_request", "@app.errorhandler",
    ],
    "django": [
        "@login_required", "@permission_required", "@csrf_exempt",
        "@require_http_methods", "@api_view",
    ],
    "fastapi": [
        "@router.get", "@router.post", "@router.put", "@router.delete",
        "@app.get", "@app.post", "@app.put", "@app.delete",
    ],
    "celery": [
        "@shared_task", "@app.task", "@celery.task",
    ],
    # TypeScript NestJS
    "nestjs": [
        "@Controller(", "@Injectable(", "@Module(",
        "@Get(", "@Post(", "@Put(", "@Delete(", "@Patch(",
        "@Inject(", "@Body(", "@Param(", "@Query(",
        "@UseGuards(", "@UseInterceptors(",
    ],
    # TypeScript Angular
    "angular": [
        "@Component(", "@NgModule(", "@Directive(",
        "@Pipe(", "@Input(", "@Output(",
    ],
}

# Body-level patterns
_BODY_PATTERNS: Dict[str, List[str]] = {
    "fastapi": ["Depends(", "HTTPException("],
    "django": ["models.Model", "models.CharField", "models.ForeignKey"],
    "sqlalchemy": ["Column(", "relationship(", "Base.metadata"],
    "react": ["useState(", "useEffect(", "useCallback(", "useMemo(", "useRef("],
    "nextjs": ["getServerSideProps", "getStaticProps", "getStaticPaths"],
    "express": ["app.get(", "app.post(", "app.use(", "router.get(", "router.post(", "router.use("],
}


class FrameworkDetector:
    """Detect frameworks from function metadata and file content."""

    def __init__(self):
        self._file_framework_cache: Dict[str, Set[str]] = {}

    def detect_from_file(self, file_path: str, content: str) -> Set[str]:
        """Detect frameworks from file-level imports. Results are cached."""
        if file_path in self._file_framework_cache:
            return self._file_framework_cache[file_path]

        frameworks: Set[str] = set()
        for fw, patterns in _IMPORT_PATTERNS.items():
            for pattern in patterns:
                if pattern in content:
                    frameworks.add(fw)
                    break

        self._file_framework_cache[file_path] = frameworks
        return frameworks

    def detect_from_function(self, func: CodeFunction, file_frameworks: Set[str] = None) -> List[str]:
        """Detect frameworks from function decorators/annotations and body patterns."""
        frameworks: Set[str] = set(file_frameworks) if file_frameworks else set()

        # Check annotations/decorators (language-aware to avoid cross-language false positives)
        decorators_str = " ".join(func.decorators)
        for fw, annotations in _ANNOTATION_PATTERNS.items():
            if not self._fw_matches_language(fw, func.language):
                continue
            for ann in annotations:
                if ann in decorators_str:
                    frameworks.add(fw)
                    break

        # Check body patterns
        body = func.body
        for fw, patterns in _BODY_PATTERNS.items():
            for pattern in patterns:
                if pattern in body:
                    frameworks.add(fw)
                    break

        # Check signature for express middleware
        if func.language in ("javascript", "typescript"):
            if re.search(r"\(req\s*,\s*res\s*,\s*next\)", func.signature):
                frameworks.add("express")

        return sorted(frameworks)

    @staticmethod
    def _fw_matches_language(fw: str, language: str) -> bool:
        """Check if a framework is relevant for the given language."""
        _FW_LANGUAGES = {
            "spring_boot": ("java",),
            "spring_mvc": ("java",),
            "jpa": ("java",),
            "lombok": ("java",),
            "flask": ("python",),
            "django": ("python",),
            "fastapi": ("python",),
            "sqlalchemy": ("python",),
            "celery": ("python",),
            "express": ("javascript", "typescript"),
            "react": ("javascript", "typescript"),
            "nextjs": ("javascript", "typescript"),
            "nestjs": ("typescript",),
            "angular": ("typescript",),
            "typeorm": ("typescript",),
            "prisma": ("typescript",),
        }
        allowed = _FW_LANGUAGES.get(fw)
        if allowed is None:
            return True  # unknown framework, allow for any language
        return language in allowed
