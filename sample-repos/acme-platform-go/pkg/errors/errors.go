package errors

import (
	"fmt"
	"net/http"
)

// AcmeError is the standard error type for all Acme services.
// Error codes follow the format: ACME-{DOMAIN}-{NUMBER}
type AcmeError struct {
	Code       string `json:"error"`
	Message    string `json:"message"`
	StatusCode int    `json:"-"`
	Cause      error  `json:"-"`
}

func (e *AcmeError) Error() string {
	if e.Cause != nil {
		return fmt.Sprintf("%s: %s: %v", e.Code, e.Message, e.Cause)
	}
	return fmt.Sprintf("%s: %s", e.Code, e.Message)
}

func (e *AcmeError) Unwrap() error {
	return e.Cause
}

// Standard Acme error constructors

func NewNotFound(domain, resource, id string) *AcmeError {
	return &AcmeError{
		Code:       fmt.Sprintf("ACME-%s-404", domain),
		Message:    fmt.Sprintf("%s not found: %s", resource, id),
		StatusCode: http.StatusNotFound,
	}
}

func NewValidation(domain, field, reason string) *AcmeError {
	return &AcmeError{
		Code:       fmt.Sprintf("ACME-%s-400", domain),
		Message:    fmt.Sprintf("validation failed: %s - %s", field, reason),
		StatusCode: http.StatusBadRequest,
	}
}

func NewInternal(domain string, cause error) *AcmeError {
	return &AcmeError{
		Code:       fmt.Sprintf("ACME-%s-500", domain),
		Message:    "internal server error",
		StatusCode: http.StatusInternalServerError,
		Cause:      cause,
	}
}

func NewUnauthorized(domain string) *AcmeError {
	return &AcmeError{
		Code:       fmt.Sprintf("ACME-%s-401", domain),
		Message:    "unauthorized",
		StatusCode: http.StatusUnauthorized,
	}
}

// WriteError writes an AcmeError as JSON to an HTTP response.
func WriteError(w http.ResponseWriter, err *AcmeError) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(err.StatusCode)
	fmt.Fprintf(w, `{"error":"%s","message":"%s"}`, err.Code, err.Message)
}
