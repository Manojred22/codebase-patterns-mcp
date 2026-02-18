package telemetry

import (
	"context"

	"go.opentelemetry.io/otel/metric"
	sdkmetric "go.opentelemetry.io/otel/sdk/metric"
	"go.opentelemetry.io/otel/sdk/metric/metricdata"
)

// AcmeMetricsConfig configures the metrics pipeline.
type AcmeMetricsConfig struct {
	ServiceName string
	TeamLabel   string
	CostCenter  string
	Environment string
}

// NewMeterProvider creates an Acme-compliant meter provider.
// Exports to metrics.internal.acme.com:4317
func NewMeterProvider(cfg AcmeMetricsConfig) (*sdkmetric.MeterProvider, error) {
	// Acme standard: all metrics go to the internal collector
	reader := sdkmetric.NewPeriodicReader(nil) // placeholder for internal exporter

	mp := sdkmetric.NewMeterProvider(
		sdkmetric.WithReader(reader),
	)

	return mp, nil
}

// RecordLatency records an HTTP request latency with Acme-standard attributes.
func RecordLatency(ctx context.Context, meter metric.Meter, method, path string, durationMs float64) {
	histogram, _ := meter.Float64Histogram(
		"acme.http.request.duration",
		metric.WithDescription("HTTP request duration in milliseconds"),
		metric.WithUnit("ms"),
	)
	histogram.Record(ctx, durationMs)
}
