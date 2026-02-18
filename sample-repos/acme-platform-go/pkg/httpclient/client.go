package httpclient

import (
	"fmt"
	"net/http"
	"time"
)

// AcmeHTTPConfig configures the standard Acme HTTP client.
type AcmeHTTPConfig struct {
	ServiceName string
	Timeout     time.Duration
	MaxRetries  int
	RetryDelay  time.Duration
}

// NewClient creates an Acme-standard HTTP client with retry, tracing, and auth propagation.
// All outgoing HTTP calls MUST use this instead of http.DefaultClient.
func NewClient(cfg AcmeHTTPConfig) *http.Client {
	if cfg.Timeout == 0 {
		cfg.Timeout = 30 * time.Second // Acme default
	}
	if cfg.MaxRetries == 0 {
		cfg.MaxRetries = 3
	}
	if cfg.RetryDelay == 0 {
		cfg.RetryDelay = 100 * time.Millisecond
	}

	transport := &acmeTransport{
		base:        http.DefaultTransport,
		serviceName: cfg.ServiceName,
		maxRetries:  cfg.MaxRetries,
		retryDelay:  cfg.RetryDelay,
	}

	return &http.Client{
		Timeout:   cfg.Timeout,
		Transport: transport,
	}
}

type acmeTransport struct {
	base        http.RoundTripper
	serviceName string
	maxRetries  int
	retryDelay  time.Duration
}

func (t *acmeTransport) RoundTrip(req *http.Request) (*http.Response, error) {
	// Inject Acme tracing headers
	req.Header.Set("X-Acme-Service", t.serviceName)
	req.Header.Set("X-Acme-Request-ID", generateRequestID())

	var lastErr error
	for attempt := 0; attempt <= t.maxRetries; attempt++ {
		resp, err := t.base.RoundTrip(req)
		if err == nil && resp.StatusCode < 500 {
			return resp, nil
		}
		lastErr = err
		if err == nil {
			lastErr = fmt.Errorf("server error: %d", resp.StatusCode)
		}
		time.Sleep(t.retryDelay * time.Duration(1<<uint(attempt)))
	}
	return nil, fmt.Errorf("acme/httpclient: all %d retries failed: %w", t.maxRetries, lastErr)
}

func generateRequestID() string {
	return fmt.Sprintf("acme-%d", time.Now().UnixNano())
}
