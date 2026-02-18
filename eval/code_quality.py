"""
Pattern conformance checker.

Scans generated code for Acme-specific markers vs generic markers.
Returns a 0.0–1.0 conformance score.
"""

import re
from typing import Dict, List, Tuple

# Acme markers by category — presence of these means the code follows team patterns
ACME_MARKERS: Dict[str, List[str]] = {
    "telemetry": [
        "AcmeTracerConfig",
        "telemetry.internal.acme.com",
        "TeamLabel",
        "team_label",
        "teamLabel",
        "CostCenter",
        "cost_center",
        "costCenter",
        "NewTracer",
        "create_acme_tracer",
        "createAcmeTracer",
        "AcmeTracerService",
    ],
    "auth": [
        "X-Acme-Auth",
        "x-acme-auth",
        "ACME-AUTH-001",
        "ACME-AUTH-002",
        "ACME-AUTH-003",
        "X-Acme-Internal-Service",
        "auth.internal.acme.com",
        "AcmeAuthMiddleware",
        "acme_auth_required",
        "createAcmeAuthMiddleware",
        "AcmeAuthGuard",
        "AcmeAuthFilter",
    ],
    "http": [
        "X-Acme-Service",
        "X-Acme-Request-ID",
        "AcmeHTTPClient",
        "AcmeHTTPConfig",
        "createAcmeHttpClient",
        "acmeTransport",
    ],
    "database": [
        "db.internal.acme.com",
        "AcmeDBConfig",
        "AcmeRepository",
        "AcmeBaseRepository",
        "AcmeSoftDeleteMixin",
        "soft_delete",
        "SoftDelete",
        "softDelete",
    ],
    "errors": [
        "AcmeError",
        "AcmeException",
        "ACME-",
        "acme/",
    ],
}

# Generic markers — presence of these (without Acme markers) means generic code
GENERIC_MARKERS: Dict[str, List[str]] = {
    "telemetry": [
        "jaeger.New",
        "jaeger.WithCollectorEndpoint",
        "localhost:14268",
        "localhost:4317",
        "localhost:16686",
        "NewExporter",
    ],
    "auth": [
        "Authorization: Bearer",
        "jwt.verify",
        "jwt.decode",
        "passport.authenticate",
    ],
    "http": [
        "http.DefaultClient",
        "requests.get(",
        "axios.get(",
        "fetch(",
    ],
    "database": [
        "localhost:5432",
        "localhost:3306",
        "hard delete",
    ],
    "errors": [
        "InternalServerError",
        "HttpException",
    ],
}


def check_code_quality(code: str, category: str) -> Dict:
    """Check generated code for Acme pattern conformance.

    Args:
        code: The generated source code to check.
        category: One of "telemetry", "auth", "http", "database", "errors".

    Returns:
        Dict with:
            score: 0.0–1.0 conformance score
            acme_markers_found: list of Acme markers found
            generic_markers_found: list of generic markers found
            verdict: "conformant", "partial", or "generic"
    """
    acme_markers = ACME_MARKERS.get(category, [])
    generic_markers = GENERIC_MARKERS.get(category, [])

    acme_found = [m for m in acme_markers if m in code]
    generic_found = [m for m in generic_markers if m in code]

    acme_count = len(acme_found)
    generic_count = len(generic_found)
    total = acme_count + generic_count

    if total == 0:
        score = 0.5  # Neutral — can't tell
        verdict = "unknown"
    elif generic_count == 0:
        score = 1.0
        verdict = "conformant"
    elif acme_count == 0:
        score = 0.0
        verdict = "generic"
    else:
        score = acme_count / total
        verdict = "partial" if score < 0.8 else "conformant"

    return {
        "score": round(score, 2),
        "acme_markers_found": acme_found,
        "generic_markers_found": generic_found,
        "verdict": verdict,
    }


def check_all_categories(code: str) -> Dict:
    """Check code against all categories and return the best-matching one."""
    results = {}
    for category in ACME_MARKERS:
        results[category] = check_code_quality(code, category)

    # Find category with most Acme markers
    best = max(results.items(), key=lambda x: len(x[1]["acme_markers_found"]))
    return {
        "best_category": best[0],
        "best_result": best[1],
        "all_categories": results,
    }
