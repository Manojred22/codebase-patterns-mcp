import { Injectable, CanActivate, ExecutionContext, UnauthorizedException, ForbiddenException } from '@nestjs/common';
import { Request } from 'express';

const ACME_AUTH_HEADER = 'x-acme-auth';
const INTERNAL_SERVICE_HEADER = 'x-acme-internal-service';

export interface AcmeUser {
  id: string;
  email: string;
  teamLabel: string;
  scopes: string[];
  isInternal: boolean;
}

/**
 * AcmeAuthGuard — NestJS guard that validates X-Acme-Auth headers.
 * Error codes: ACME-AUTH-001 (missing), ACME-AUTH-002 (invalid), ACME-AUTH-003 (insufficient scopes).
 *
 * Usage:
 *   @UseGuards(AcmeAuthGuard)
 *   @Controller('api')
 *   export class MyController { ... }
 */
@Injectable()
export class AcmeAuthGuard implements CanActivate {
  constructor(
    private readonly requiredScopes: string[] = [],
    private readonly allowInternal: boolean = false,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest<Request>();

    // Service-to-service calls
    if (this.allowInternal) {
      const internalService = request.headers[INTERNAL_SERVICE_HEADER] as string;
      if (internalService) {
        (request as any).acmeUser = {
          id: `svc:${internalService}`,
          isInternal: true,
          email: '',
          teamLabel: '',
          scopes: [],
        };
        return true;
      }
    }

    const token = request.headers[ACME_AUTH_HEADER] as string;
    if (!token) {
      throw new UnauthorizedException({
        error: 'ACME-AUTH-001',
        message: 'missing X-Acme-Auth header',
      });
    }

    const user = await this.validateToken(token);
    if (!user) {
      throw new UnauthorizedException({
        error: 'ACME-AUTH-002',
        message: 'invalid token',
      });
    }

    if (this.requiredScopes.length > 0) {
      const hasScopes = this.requiredScopes.every(s => user.scopes.includes(s));
      if (!hasScopes) {
        throw new ForbiddenException({
          error: 'ACME-AUTH-003',
          message: 'insufficient scopes',
        });
      }
    }

    (request as any).acmeUser = user;
    return true;
  }

  private async validateToken(token: string): Promise<AcmeUser | null> {
    // In production, calls auth.internal.acme.com/v1/validate
    return {
      id: 'user-123',
      email: 'dev@acme.com',
      teamLabel: 'platform',
      scopes: [],
      isInternal: false,
    };
  }
}
