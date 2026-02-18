package com.acme.platform.errors;

import org.springframework.http.HttpStatus;

/**
 * AcmeException — standard exception for all Acme Java services.
 * Error codes follow the format: ACME-{DOMAIN}-{NUMBER}
 */
public class AcmeException extends RuntimeException {

    private final String errorCode;
    private final HttpStatus httpStatus;

    public AcmeException(String domain, int code, String message, HttpStatus status) {
        super(message);
        this.errorCode = String.format("ACME-%s-%03d", domain, code);
        this.httpStatus = status;
    }

    public String getErrorCode() { return errorCode; }
    public HttpStatus getHttpStatus() { return httpStatus; }

    public static AcmeException notFound(String domain, String resource, String id) {
        return new AcmeException(domain, 404,
                String.format("%s not found: %s", resource, id), HttpStatus.NOT_FOUND);
    }

    public static AcmeException validation(String domain, String field, String reason) {
        return new AcmeException(domain, 400,
                String.format("validation failed: %s - %s", field, reason), HttpStatus.BAD_REQUEST);
    }

    public static AcmeException internal(String domain, Throwable cause) {
        AcmeException ex = new AcmeException(domain, 500,
                "internal server error", HttpStatus.INTERNAL_SERVER_ERROR);
        ex.initCause(cause);
        return ex;
    }

    public static AcmeException unauthorized(String domain) {
        return new AcmeException(domain, 401, "unauthorized", HttpStatus.UNAUTHORIZED);
    }
}
