"""
Ground truth test queries for evaluating search quality.

Each query has expected function IDs (exact match) and regex patterns (fuzzy match).
Function IDs follow the format: "repo_name/file_path:function_name"

Updated after first index run to match actual indexed IDs.
"""

import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class TestQuery:
    """A test query with ground truth expected results."""

    id: str
    query: str
    category: str
    expected_ids: List[str] = field(default_factory=list)
    expected_id_patterns: List[str] = field(default_factory=list)


# 8 test queries covering telemetry, auth, HTTP clients, database repos, error handling, metrics
# expected_ids updated from actual index run (2026-02-18)
GROUND_TRUTH_QUERIES: List[TestQuery] = [
    TestQuery(
        id="telemetry-go",
        query="add telemetry tracing to a Go service",
        category="telemetry",
        expected_ids=[
            "acme-platform-go/pkg/telemetry/tracer.go:NewTracer",
            "acme-platform-go/pkg/telemetry/tracer.go:Shutdown",
            "acme-platform-go/pkg/telemetry/metrics.go:RecordLatency",
        ],
        expected_id_patterns=[
            r"acme-platform-go.*telemetry.*:NewTracer",
            r"acme-platform-go.*telemetry.*:Shutdown",
            r"acme-platform-go.*telemetry.*:RecordLatency",
        ],
    ),
    TestQuery(
        id="telemetry-python",
        query="set up OpenTelemetry tracing in Python with compliance fields",
        category="telemetry",
        expected_ids=[
            "acme-platform-python/acme/telemetry/tracer.py:create_acme_tracer",
            "acme-platform-python/acme/telemetry/tracer.py:AcmeTracerConfig",
            "acme-platform-python/acme/telemetry/tracer.py:AcmeTracerConfig.__init__",
        ],
        expected_id_patterns=[
            r"acme-platform-python.*telemetry.*:create_acme_tracer",
            r"acme-platform-python.*telemetry.*:AcmeTracerConfig$",
            r"acme-platform-python.*telemetry.*:AcmeTracerConfig\.__init__",
        ],
    ),
    TestQuery(
        id="auth-middleware",
        query="authentication middleware with token validation",
        category="auth",
        expected_ids=[
            "acme-platform-js/src/middleware/auth.js:validateToken",
            "acme-platform-go/pkg/auth/middleware.go:validateToken",
            "acme-platform-ts/src/auth/auth.guard.ts:AcmeAuthGuard.validateToken",
            "acme-platform-python/acme/auth/middleware.py:_validate_token",
            "acme-platform-js/src/middleware/auth.js:createAcmeAuthMiddleware",
        ],
        expected_id_patterns=[
            r"acme-platform-.*auth.*:.*[Vv]alidate[Tt]oken",
            r"acme-platform-js.*auth.*:createAcmeAuthMiddleware",
            r"acme-platform-go.*auth.*:NewAuthMiddleware",
        ],
    ),
    TestQuery(
        id="http-client",
        query="HTTP client with retry and request tracing headers",
        category="http",
        expected_ids=[
            "acme-platform-python/acme/http/client.py:AcmeHTTPClient",
            "acme-platform-js/src/http/client.js:createAcmeHttpClient",
            "acme-platform-go/pkg/httpclient/client.go:RoundTrip",
        ],
        expected_id_patterns=[
            r"acme-platform-python.*http.*client.*:AcmeHTTPClient$",
            r"acme-platform-js.*http.*client.*:createAcmeHttpClient",
            r"acme-platform-go.*httpclient.*:(NewClient|RoundTrip)",
        ],
    ),
    TestQuery(
        id="database-repository",
        query="database repository with soft delete and CRUD operations",
        category="database",
        expected_ids=[
            "acme-platform-ts/src/database/base.repository.ts:AcmeBaseRepository.softDelete",
            "acme-platform-go/pkg/database/repository.go:SoftDelete",
            "acme-platform-python/acme/db/repository.py:AcmeRepository.soft_delete",
            "acme-platform-ts/src/database/base.repository.ts:AcmeBaseRepository",
            "acme-platform-python/acme/db/repository.py:AcmeSoftDeleteMixin",
        ],
        expected_id_patterns=[
            r"acme-platform-ts.*database.*:AcmeBaseRepository",
            r"acme-platform-go.*database.*:(SoftDelete|NewRepository)",
            r"acme-platform-python.*db.*repository.*:(AcmeRepository|AcmeSoftDeleteMixin)",
        ],
    ),
    TestQuery(
        id="error-handling",
        query="standardized error handling with error codes",
        category="errors",
        expected_ids=[
            "acme-platform-js/src/errors/acme-error.js:acmeErrorHandler",
            "acme-platform-java/src/main/java/com/acme/platform/errors/AcmeException.java:AcmeException.getErrorCode",
            "acme-platform-js/src/errors/acme-error.js:AcmeError",
            "acme-platform-python/acme/errors/exceptions.py:AcmeError",
        ],
        expected_id_patterns=[
            r"acme-platform-js.*errors.*:AcmeError$",
            r"acme-platform-python.*errors.*:AcmeError$",
            r"acme-platform-java.*errors.*:AcmeException",
            r"acme-platform-js.*errors.*:acmeErrorHandler",
        ],
    ),
    TestQuery(
        id="telemetry-java",
        query="Spring Boot telemetry tracing service with OpenTelemetry",
        category="telemetry",
        expected_ids=[
            "acme-platform-java/src/main/java/com/acme/platform/telemetry/AcmeTracer.java:AcmeTracer",
            "acme-platform-java/src/main/java/com/acme/platform/telemetry/AcmeTracer.java:AcmeTracer.initialize",
            "acme-platform-java/src/main/java/com/acme/platform/telemetry/AcmeTracerConfig.java:AcmeTracerConfig",
        ],
        expected_id_patterns=[
            r"acme-platform-java.*telemetry.*AcmeTracer\.java:AcmeTracer$",
            r"acme-platform-java.*telemetry.*:AcmeTracer\.initialize",
            r"acme-platform-java.*telemetry.*:AcmeTracerConfig$",
        ],
    ),
    TestQuery(
        id="nestjs-auth",
        query="NestJS authentication guard with role-based access",
        category="auth",
        expected_ids=[
            "acme-platform-ts/src/auth/auth.guard.ts:AcmeAuthGuard.canActivate",
            "acme-platform-ts/src/auth/auth.guard.ts:AcmeAuthGuard",
            "acme-platform-ts/src/auth/auth.guard.ts:AcmeAuthGuard.validateToken",
        ],
        expected_id_patterns=[
            r"acme-platform-ts.*auth.*:AcmeAuthGuard$",
            r"acme-platform-ts.*auth.*:AcmeAuthGuard\.canActivate",
            r"acme-platform-ts.*auth.*:AcmeAuthGuard\.validateToken",
        ],
    ),
]


def match_id(actual_id: str, expected_id: str) -> bool:
    """Check if an actual ID matches an expected ID (exact match)."""
    return actual_id == expected_id


def match_id_pattern(actual_id: str, pattern: str) -> bool:
    """Check if an actual ID matches a regex pattern (fuzzy match)."""
    return bool(re.search(pattern, actual_id))
