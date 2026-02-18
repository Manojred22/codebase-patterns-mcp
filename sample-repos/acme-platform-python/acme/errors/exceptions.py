"""
Acme Error Handling — standard exceptions for all Python services.

Error codes follow the format: ACME-{DOMAIN}-{NUMBER}
"""

from flask import jsonify


class AcmeError(Exception):
    """Standard error type for all Acme Python services."""

    def __init__(self, domain: str, code: int, message: str, status_code: int = 500):
        super().__init__(message)
        self.error_code = f"ACME-{domain}-{code:03d}"
        self.message = message
        self.status_code = status_code

    def to_response(self):
        """Convert to a Flask JSON response."""
        return jsonify({"error": self.error_code, "message": self.message}), self.status_code


class AcmeNotFoundError(AcmeError):
    def __init__(self, domain: str, resource: str, id: str):
        super().__init__(domain, 404, f"{resource} not found: {id}", 404)


class AcmeValidationError(AcmeError):
    def __init__(self, domain: str, field: str, reason: str):
        super().__init__(domain, 400, f"validation failed: {field} - {reason}", 400)


class AcmeUnauthorizedError(AcmeError):
    def __init__(self, domain: str):
        super().__init__(domain, 401, "unauthorized", 401)


def register_error_handlers(app):
    """Register Acme error handlers on a Flask app."""

    @app.errorhandler(AcmeError)
    def handle_acme_error(error):
        return error.to_response()
