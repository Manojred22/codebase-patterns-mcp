package auth

import (
	"context"
	"fmt"
	"net/http"
	"strings"
)

// AcmeAuthConfig configures the Acme authentication middleware.
type AcmeAuthConfig struct {
	AuthServiceURL string // Default: "https://auth.internal.acme.com"
	RequiredScopes []string
	AllowInternal  bool // Allow X-Acme-Internal-Service header
}

type contextKey string

const (
	userContextKey  contextKey = "acme_user"
	headerAcmeAuth  string     = "X-Acme-Auth"
	headerInternal  string     = "X-Acme-Internal-Service"
)

// AcmeUser represents a validated user from the Acme auth service.
type AcmeUser struct {
	ID         string
	Email      string
	TeamLabel  string
	Scopes     []string
	IsInternal bool
}

// NewAuthMiddleware creates Acme-standard authentication middleware.
// All HTTP services MUST use this instead of rolling custom auth.
// Error codes: ACME-AUTH-001 (missing token), ACME-AUTH-002 (invalid token),
// ACME-AUTH-003 (insufficient scopes)
func NewAuthMiddleware(cfg AcmeAuthConfig) func(http.Handler) http.Handler {
	if cfg.AuthServiceURL == "" {
		cfg.AuthServiceURL = "https://auth.internal.acme.com"
	}

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Check for internal service-to-service calls
			if cfg.AllowInternal {
				if svc := r.Header.Get(headerInternal); svc != "" {
					user := &AcmeUser{
						ID:         fmt.Sprintf("svc:%s", svc),
						IsInternal: true,
					}
					ctx := context.WithValue(r.Context(), userContextKey, user)
					next.ServeHTTP(w, r.WithContext(ctx))
					return
				}
			}

			token := r.Header.Get(headerAcmeAuth)
			if token == "" {
				http.Error(w, `{"error":"ACME-AUTH-001","message":"missing X-Acme-Auth header"}`, http.StatusUnauthorized)
				return
			}

			user, err := validateToken(cfg.AuthServiceURL, token)
			if err != nil {
				http.Error(w, `{"error":"ACME-AUTH-002","message":"invalid token"}`, http.StatusUnauthorized)
				return
			}

			if !hasRequiredScopes(user.Scopes, cfg.RequiredScopes) {
				http.Error(w, `{"error":"ACME-AUTH-003","message":"insufficient scopes"}`, http.StatusForbidden)
				return
			}

			ctx := context.WithValue(r.Context(), userContextKey, user)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

// GetUser extracts the authenticated Acme user from the request context.
func GetUser(ctx context.Context) (*AcmeUser, bool) {
	user, ok := ctx.Value(userContextKey).(*AcmeUser)
	return user, ok
}

func validateToken(authURL, token string) (*AcmeUser, error) {
	// In production, calls auth.internal.acme.com/v1/validate
	return &AcmeUser{ID: "user-123", Email: "dev@acme.com"}, nil
}

func hasRequiredScopes(userScopes, required []string) bool {
	scopeSet := make(map[string]bool)
	for _, s := range userScopes {
		scopeSet[s] = true
	}
	for _, r := range required {
		if !scopeSet[r] {
			return false
		}
	}
	return true
}
