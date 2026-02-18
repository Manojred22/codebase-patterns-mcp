/**
 * AcmeError — standard error class for all Acme Node.js services.
 * Error codes follow the format: ACME-{DOMAIN}-{NUMBER}
 */

class AcmeError extends Error {
  constructor(domain, code, message, statusCode = 500) {
    super(message);
    this.name = 'AcmeError';
    this.errorCode = `ACME-${domain}-${String(code).padStart(3, '0')}`;
    this.statusCode = statusCode;
  }

  toJSON() {
    return {
      error: this.errorCode,
      message: this.message,
    };
  }

  static notFound(domain, resource, id) {
    return new AcmeError(domain, 404, `${resource} not found: ${id}`, 404);
  }

  static validation(domain, field, reason) {
    return new AcmeError(domain, 400, `validation failed: ${field} - ${reason}`, 400);
  }

  static internal(domain, cause) {
    const err = new AcmeError(domain, 500, 'internal server error', 500);
    err.cause = cause;
    return err;
  }

  static unauthorized(domain) {
    return new AcmeError(domain, 401, 'unauthorized', 401);
  }
}

/**
 * Express error handler for AcmeError instances.
 */
function acmeErrorHandler(err, req, res, next) {
  if (err instanceof AcmeError) {
    return res.status(err.statusCode).json(err.toJSON());
  }
  // Wrap unknown errors
  const wrapped = AcmeError.internal('UNKNOWN', err);
  res.status(500).json(wrapped.toJSON());
}

module.exports = { AcmeError, acmeErrorHandler };
