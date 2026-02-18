import { HttpException, HttpStatus } from '@nestjs/common';

/**
 * AcmeError — standard error class for all Acme TypeScript services.
 * Error codes follow the format: ACME-{DOMAIN}-{NUMBER}
 */
export class AcmeError extends HttpException {
  public readonly errorCode: string;

  constructor(domain: string, code: number, message: string, status: HttpStatus) {
    super({ error: `ACME-${domain}-${String(code).padStart(3, '0')}`, message }, status);
    this.errorCode = `ACME-${domain}-${String(code).padStart(3, '0')}`;
  }

  static notFound(domain: string, resource: string, id: string): AcmeError {
    return new AcmeError(domain, 404, `${resource} not found: ${id}`, HttpStatus.NOT_FOUND);
  }

  static validation(domain: string, field: string, reason: string): AcmeError {
    return new AcmeError(domain, 400, `validation failed: ${field} - ${reason}`, HttpStatus.BAD_REQUEST);
  }

  static internal(domain: string, cause?: Error): AcmeError {
    const err = new AcmeError(domain, 500, 'internal server error', HttpStatus.INTERNAL_SERVER_ERROR);
    if (cause) {
      err.cause = cause;
    }
    return err;
  }

  static unauthorized(domain: string): AcmeError {
    return new AcmeError(domain, 401, 'unauthorized', HttpStatus.UNAUTHORIZED);
  }
}
