"""
Acme Authentication Middleware for Flask.

Validates X-Acme-Auth header on every request.
Error codes: ACME-AUTH-001 (missing), ACME-AUTH-002 (invalid), ACME-AUTH-003 (insufficient scopes).
"""

import functools
from flask import request, jsonify, g


class AcmeUser:
    """Represents a validated user from the Acme auth service."""

    def __init__(self, user_id: str, email: str, team_label: str, scopes: list = None, is_internal: bool = False):
        self.user_id = user_id
        self.email = email
        self.team_label = team_label
        self.scopes = scopes or []
        self.is_internal = is_internal


def acme_auth_required(scopes: list = None, allow_internal: bool = False):
    """Decorator for Acme-standard authentication on Flask routes.

    All HTTP endpoints MUST use this instead of rolling custom auth.

    Usage:
        @app.route("/api/data")
        @acme_auth_required(scopes=["read:data"])
        def get_data():
            user = g.acme_user
            ...
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            # Check for internal service-to-service calls
            if allow_internal:
                internal_service = request.headers.get("X-Acme-Internal-Service")
                if internal_service:
                    g.acme_user = AcmeUser(
                        user_id=f"svc:{internal_service}",
                        email="",
                        team_label="",
                        is_internal=True,
                    )
                    return f(*args, **kwargs)

            token = request.headers.get("X-Acme-Auth")
            if not token:
                return jsonify({"error": "ACME-AUTH-001", "message": "missing X-Acme-Auth header"}), 401

            user = _validate_token(token)
            if not user:
                return jsonify({"error": "ACME-AUTH-002", "message": "invalid token"}), 401

            if scopes and not _has_required_scopes(user.scopes, scopes):
                return jsonify({"error": "ACME-AUTH-003", "message": "insufficient scopes"}), 403

            g.acme_user = user
            return f(*args, **kwargs)

        return wrapper
    return decorator


def _validate_token(token: str) -> AcmeUser:
    """Validate token against auth.internal.acme.com/v1/validate."""
    # In production, this calls the Acme auth service
    return AcmeUser(user_id="user-123", email="dev@acme.com", team_label="platform")


def _has_required_scopes(user_scopes: list, required: list) -> bool:
    return all(s in user_scopes for s in required)
