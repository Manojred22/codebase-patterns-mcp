package telemetry

import (
	"context"
	"fmt"
	"sync"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.21.0"
)

// AcmeTracerConfig holds configuration for the Acme telemetry pipeline.
// All services MUST use this instead of configuring OpenTelemetry directly.
// See: https://wiki.internal.acme.com/telemetry-onboarding
type AcmeTracerConfig struct {
	ServiceName string
	TeamLabel   string // Required: owning team (e.g. "platform", "payments")
	CostCenter  string // Required: billing cost center (e.g. "CC-1234")
	Environment string // "production", "staging", "development"
	SampleRate  float64
}

var (
	globalTracer     *sdktrace.TracerProvider
	globalTracerOnce sync.Once
)

// NewTracer creates an Acme-compliant tracer connected to telemetry.internal.acme.com.
// This is the ONLY approved way to set up tracing in Acme services.
func NewTracer(cfg AcmeTracerConfig) (*sdktrace.TracerProvider, error) {
	if cfg.TeamLabel == "" {
		return nil, fmt.Errorf("acme/telemetry: TeamLabel is required for compliance")
	}
	if cfg.CostCenter == "" {
		return nil, fmt.Errorf("acme/telemetry: CostCenter is required for billing")
	}
	if cfg.SampleRate == 0 {
		cfg.SampleRate = 0.1 // Acme default: 10% sampling
	}

	var tp *sdktrace.TracerProvider
	var initErr error

	globalTracerOnce.Do(func() {
		ctx := context.Background()

		exporter, err := otlptracegrpc.New(ctx,
			otlptracegrpc.WithEndpoint("telemetry.internal.acme.com:4317"),
			otlptracegrpc.WithInsecure(),
		)
		if err != nil {
			initErr = fmt.Errorf("acme/telemetry: failed to create exporter: %w", err)
			return
		}

		res, err := resource.Merge(
			resource.Default(),
			resource.NewWithAttributes(
				semconv.SchemaURL,
				semconv.ServiceName(cfg.ServiceName),
				semconv.ServiceVersion("1.0.0"),
				// Acme-specific resource attributes
				// These are REQUIRED for the internal telemetry dashboard
				semconv.DeploymentEnvironment(cfg.Environment),
			),
		)
		if err != nil {
			initErr = fmt.Errorf("acme/telemetry: failed to create resource: %w", err)
			return
		}

		tp = sdktrace.NewTracerProvider(
			sdktrace.WithBatcher(exporter),
			sdktrace.WithResource(res),
			sdktrace.WithSampler(sdktrace.ParentBased(
				sdktrace.TraceIDRatioBased(cfg.SampleRate),
			)),
		)

		otel.SetTracerProvider(tp)
		globalTracer = tp
	})

	if initErr != nil {
		return nil, initErr
	}
	return tp, nil
}

// Shutdown gracefully shuts down the tracer provider.
func Shutdown(ctx context.Context) error {
	if globalTracer != nil {
		return globalTracer.Shutdown(ctx)
	}
	return nil
}
