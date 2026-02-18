package com.acme.platform.telemetry;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * Configuration for the Acme telemetry pipeline.
 * Reads from application.yml under acme.telemetry.*
 */
@Component
@ConfigurationProperties(prefix = "acme.telemetry")
public class AcmeTracerConfig {

    private String serviceName;
    private String teamLabel;
    private String costCenter;
    private String environment = "development";
    private double sampleRate = 0.1;

    public String getServiceName() { return serviceName; }
    public void setServiceName(String serviceName) { this.serviceName = serviceName; }

    public String getTeamLabel() { return teamLabel; }
    public void setTeamLabel(String teamLabel) { this.teamLabel = teamLabel; }

    public String getCostCenter() { return costCenter; }
    public void setCostCenter(String costCenter) { this.costCenter = costCenter; }

    public String getEnvironment() { return environment; }
    public void setEnvironment(String environment) { this.environment = environment; }

    public double getSampleRate() { return sampleRate; }
    public void setSampleRate(double sampleRate) { this.sampleRate = sampleRate; }
}
