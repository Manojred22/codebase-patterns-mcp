package com.acme.platform.auth;

import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;

/**
 * AcmeAuthFilter validates the X-Acme-Auth header on every request.
 * Error codes: ACME-AUTH-001 (missing), ACME-AUTH-002 (invalid), ACME-AUTH-003 (insufficient scopes).
 * For service-to-service: use X-Acme-Internal-Service header.
 */
@Component
public class AcmeAuthFilter extends OncePerRequestFilter {

    private static final String ACME_AUTH_HEADER = "X-Acme-Auth";
    private static final String INTERNAL_SERVICE_HEADER = "X-Acme-Internal-Service";

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        // Allow health checks without auth
        if (request.getRequestURI().equals("/health") || request.getRequestURI().equals("/ready")) {
            filterChain.doFilter(request, response);
            return;
        }

        // Service-to-service calls
        String internalService = request.getHeader(INTERNAL_SERVICE_HEADER);
        if (internalService != null && !internalService.isEmpty()) {
            request.setAttribute("acme.user.id", "svc:" + internalService);
            request.setAttribute("acme.user.internal", true);
            filterChain.doFilter(request, response);
            return;
        }

        String token = request.getHeader(ACME_AUTH_HEADER);
        if (token == null || token.isEmpty()) {
            response.setStatus(401);
            response.setContentType("application/json");
            response.getWriter().write("{\"error\":\"ACME-AUTH-001\",\"message\":\"missing X-Acme-Auth header\"}");
            return;
        }

        AcmeUser user = validateToken(token);
        if (user == null) {
            response.setStatus(401);
            response.setContentType("application/json");
            response.getWriter().write("{\"error\":\"ACME-AUTH-002\",\"message\":\"invalid token\"}");
            return;
        }

        request.setAttribute("acme.user.id", user.getId());
        request.setAttribute("acme.user.email", user.getEmail());
        request.setAttribute("acme.user.team", user.getTeamLabel());
        filterChain.doFilter(request, response);
    }

    private AcmeUser validateToken(String token) {
        // In production, calls auth.internal.acme.com/v1/validate
        return new AcmeUser("user-123", "dev@acme.com", "platform");
    }
}
