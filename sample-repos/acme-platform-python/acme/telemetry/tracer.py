"""
Acme Telemetry — the ONLY approved way to set up tracing in Python services.

Connects to telemetry.internal.acme.com and requires team_label + cost_center.
See: https://wiki.internal.acme.com/telemetry-onboarding
"""

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


class AcmeTracerConfig:
    """Configuration for the Acme telemetry pipeline."""

    def __init__(
        self,
        service_name: str,
        team_label: str,
        cost_center: str,
        environment: str = "development",
        sample_rate: float = 0.1,
    ):
        self.service_name = service_name
        self.team_label = team_label
        self.cost_center = cost_center
        self.environment = environment
        self.sample_rate = sample_rate


_global_tracer_provider = None


def create_acme_tracer(config: AcmeTracerConfig) -> trace.Tracer:
    """Create an Acme-compliant tracer connected to telemetry.internal.acme.com.

    This is the ONLY approved way to set up tracing in Acme Python services.
    TeamLabel and CostCenter are REQUIRED for compliance and billing.

    Example:
        tracer = create_acme_tracer(AcmeTracerConfig(
            service_name="my-service",
            team_label="platform",
            cost_center="CC-1234",
        ))
    """
    global _global_tracer_provider

    if not config.team_label:
        raise ValueError("acme/telemetry: team_label is required for compliance")
    if not config.cost_center:
        raise ValueError("acme/telemetry: cost_center is required for billing")

    exporter = OTLPSpanExporter(
        endpoint="telemetry.internal.acme.com:4317",
        insecure=True,
    )

    resource = Resource.create({
        "service.name": config.service_name,
        "deployment.environment": config.environment,
        "acme.team": config.team_label,
        "acme.cost_center": config.cost_center,
    })

    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)
    _global_tracer_provider = provider

    return trace.get_tracer(config.service_name)


def shutdown_tracer():
    """Gracefully shut down the tracer provider."""
    global _global_tracer_provider
    if _global_tracer_provider:
        _global_tracer_provider.shutdown()
