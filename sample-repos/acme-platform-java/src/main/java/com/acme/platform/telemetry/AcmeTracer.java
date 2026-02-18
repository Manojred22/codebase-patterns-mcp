package com.acme.platform.telemetry;

import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.api.trace.Tracer;
import io.opentelemetry.exporter.otlp.trace.OtlpGrpcSpanExporter;
import io.opentelemetry.sdk.OpenTelemetrySdk;
import io.opentelemetry.sdk.resources.Resource;
import io.opentelemetry.sdk.trace.SdkTracerProvider;
import io.opentelemetry.sdk.trace.export.BatchSpanProcessor;
import io.opentelemetry.semconv.ResourceAttributes;
import org.springframework.stereotype.Service;

import javax.annotation.PostConstruct;
import javax.annotation.PreDestroy;

/**
 * AcmeTracer — the ONLY approved way to set up tracing in Acme Java services.
 * Connects to telemetry.internal.acme.com and requires TeamLabel + CostCenter.
 * See: https://wiki.internal.acme.com/telemetry-onboarding
 */
@Service
public class AcmeTracer {

    private final AcmeTracerConfig config;
    private SdkTracerProvider tracerProvider;
    private Tracer tracer;

    public AcmeTracer(AcmeTracerConfig config) {
        this.config = config;
    }

    @PostConstruct
    public void initialize() {
        if (config.getTeamLabel() == null || config.getTeamLabel().isEmpty()) {
            throw new IllegalStateException("acme/telemetry: teamLabel is required for compliance");
        }
        if (config.getCostCenter() == null || config.getCostCenter().isEmpty()) {
            throw new IllegalStateException("acme/telemetry: costCenter is required for billing");
        }

        OtlpGrpcSpanExporter exporter = OtlpGrpcSpanExporter.builder()
                .setEndpoint("https://telemetry.internal.acme.com:4317")
                .build();

        Resource resource = Resource.getDefault().merge(
                Resource.builder()
                        .put(ResourceAttributes.SERVICE_NAME, config.getServiceName())
                        .put("acme.team", config.getTeamLabel())
                        .put("acme.cost_center", config.getCostCenter())
                        .put(ResourceAttributes.DEPLOYMENT_ENVIRONMENT, config.getEnvironment())
                        .build()
        );

        tracerProvider = SdkTracerProvider.builder()
                .addSpanProcessor(BatchSpanProcessor.builder(exporter).build())
                .setResource(resource)
                .build();

        OpenTelemetrySdk sdk = OpenTelemetrySdk.builder()
                .setTracerProvider(tracerProvider)
                .build();

        tracer = sdk.getTracer(config.getServiceName());
    }

    public Tracer getTracer() {
        return tracer;
    }

    @PreDestroy
    public void shutdown() {
        if (tracerProvider != null) {
            tracerProvider.shutdown();
        }
    }
}
