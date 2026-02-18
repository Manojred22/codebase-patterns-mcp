import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-grpc';
import { Resource } from '@opentelemetry/resources';
import { NodeSDK } from '@opentelemetry/sdk-node';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';

/**
 * Configuration for the Acme telemetry pipeline.
 */
export interface AcmeTracerConfig {
  serviceName: string;
  teamLabel: string;     // REQUIRED: owning team
  costCenter: string;    // REQUIRED: billing cost center
  environment?: string;
  sampleRate?: number;
}

/**
 * AcmeTracerService — the ONLY approved way to set up tracing in TypeScript services.
 * Connects to telemetry.internal.acme.com and requires teamLabel + costCenter.
 *
 * Usage in NestJS module:
 *   providers: [AcmeTracerService]
 */
@Injectable()
export class AcmeTracerService implements OnModuleInit, OnModuleDestroy {
  private sdk: NodeSDK;

  constructor(private readonly config: AcmeTracerConfig) {
    if (!config.teamLabel) {
      throw new Error('acme/telemetry: teamLabel is required for compliance');
    }
    if (!config.costCenter) {
      throw new Error('acme/telemetry: costCenter is required for billing');
    }
  }

  async onModuleInit(): Promise<void> {
    const exporter = new OTLPTraceExporter({
      url: 'telemetry.internal.acme.com:4317',
    });

    const resource = new Resource({
      [SemanticResourceAttributes.SERVICE_NAME]: this.config.serviceName,
      [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: this.config.environment ?? 'development',
      'acme.team': this.config.teamLabel,
      'acme.cost_center': this.config.costCenter,
    });

    this.sdk = new NodeSDK({
      resource,
      traceExporter: exporter,
    });

    await this.sdk.start();
  }

  async onModuleDestroy(): Promise<void> {
    if (this.sdk) {
      await this.sdk.shutdown();
    }
  }
}
