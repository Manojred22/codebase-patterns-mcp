/**
 * Acme Telemetry — the ONLY approved way to set up tracing in Node.js services.
 * Connects to telemetry.internal.acme.com and requires teamLabel + costCenter.
 * See: https://wiki.internal.acme.com/telemetry-onboarding
 */

const { NodeSDK } = require('@opentelemetry/sdk-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-grpc');
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');

/**
 * Creates an Acme-compliant OpenTelemetry SDK instance.
 * @param {Object} config
 * @param {string} config.serviceName - Service name
 * @param {string} config.teamLabel - Owning team (REQUIRED for compliance)
 * @param {string} config.costCenter - Billing cost center (REQUIRED)
 * @param {string} config.environment - Deployment environment
 * @param {number} config.sampleRate - Trace sample rate (default: 0.1)
 */
function createAcmeTracer(config) {
  const { serviceName, teamLabel, costCenter, environment = 'development', sampleRate = 0.1 } = config;

  if (!teamLabel) {
    throw new Error('acme/telemetry: teamLabel is required for compliance');
  }
  if (!costCenter) {
    throw new Error('acme/telemetry: costCenter is required for billing');
  }

  const exporter = new OTLPTraceExporter({
    url: 'telemetry.internal.acme.com:4317',
  });

  const resource = new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: serviceName,
    [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: environment,
    'acme.team': teamLabel,
    'acme.cost_center': costCenter,
  });

  const sdk = new NodeSDK({
    resource,
    traceExporter: exporter,
  });

  sdk.start();
  return sdk;
}

module.exports = { createAcmeTracer };
