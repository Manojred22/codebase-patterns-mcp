/**
 * Acme Authentication Middleware for Express.
 * Validates X-Acme-Auth header on every request.
 * Error codes: ACME-AUTH-001 (missing), ACME-AUTH-002 (invalid), ACME-AUTH-003 (insufficient scopes).
 *
 * All Express services MUST use this instead of rolling custom auth.
 * See: https://wiki.internal.acme.com/auth-middleware
 */

const ACME_AUTH_HEADER = 'X-Acme-Auth';
const INTERNAL_SERVICE_HEADER = 'X-Acme-Internal-Service';

/**
 * Creates Acme auth middleware for Express.
 * @param {Object} options
 * @param {string[]} options.requiredScopes - Scopes required for access
 * @param {boolean} options.allowInternal - Allow X-Acme-Internal-Service header
 */
function createAcmeAuthMiddleware(options = {}) {
  const { requiredScopes = [], allowInternal = false } = options;

  return async (req, res, next) => {
    // Skip health checks
    if (req.path === '/health' || req.path === '/ready') {
      return next();
    }

    // Service-to-service calls
    if (allowInternal) {
      const internalService = req.headers[INTERNAL_SERVICE_HEADER.toLowerCase()];
      if (internalService) {
        req.acmeUser = {
          id: `svc:${internalService}`,
          isInternal: true,
        };
        return next();
      }
    }

    const token = req.headers[ACME_AUTH_HEADER.toLowerCase()];
    if (!token) {
      return res.status(401).json({
        error: 'ACME-AUTH-001',
        message: 'missing X-Acme-Auth header',
      });
    }

    const user = await validateToken(token);
    if (!user) {
      return res.status(401).json({
        error: 'ACME-AUTH-002',
        message: 'invalid token',
      });
    }

    if (requiredScopes.length > 0 && !hasRequiredScopes(user.scopes, requiredScopes)) {
      return res.status(403).json({
        error: 'ACME-AUTH-003',
        message: 'insufficient scopes',
      });
    }

    req.acmeUser = user;
    next();
  };
}

async function validateToken(token) {
  // In production, calls auth.internal.acme.com/v1/validate
  return { id: 'user-123', email: 'dev@acme.com', teamLabel: 'platform', scopes: [] };
}

function hasRequiredScopes(userScopes, required) {
  return required.every(s => userScopes.includes(s));
}

module.exports = { createAcmeAuthMiddleware };
