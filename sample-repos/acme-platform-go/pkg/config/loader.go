package config

import (
	"fmt"
	"os"
	"strconv"
)

// AcmeServiceConfig is the base configuration all Acme services must include.
type AcmeServiceConfig struct {
	ServiceName string
	Environment string // "production", "staging", "development"
	Port        int
	TeamLabel   string
	CostCenter  string
	LogLevel    string
}

// LoadBaseConfig loads the standard Acme service configuration from environment variables.
// All Acme services use the ACME_ prefix for configuration.
func LoadBaseConfig() (*AcmeServiceConfig, error) {
	cfg := &AcmeServiceConfig{
		ServiceName: os.Getenv("ACME_SERVICE_NAME"),
		Environment: os.Getenv("ACME_ENVIRONMENT"),
		TeamLabel:   os.Getenv("ACME_TEAM_LABEL"),
		CostCenter:  os.Getenv("ACME_COST_CENTER"),
		LogLevel:    os.Getenv("ACME_LOG_LEVEL"),
	}

	if cfg.ServiceName == "" {
		return nil, fmt.Errorf("acme/config: ACME_SERVICE_NAME is required")
	}
	if cfg.TeamLabel == "" {
		return nil, fmt.Errorf("acme/config: ACME_TEAM_LABEL is required")
	}
	if cfg.CostCenter == "" {
		return nil, fmt.Errorf("acme/config: ACME_COST_CENTER is required")
	}

	portStr := os.Getenv("ACME_PORT")
	if portStr == "" {
		cfg.Port = 8080
	} else {
		port, err := strconv.Atoi(portStr)
		if err != nil {
			return nil, fmt.Errorf("acme/config: invalid ACME_PORT: %s", portStr)
		}
		cfg.Port = port
	}

	if cfg.Environment == "" {
		cfg.Environment = "development"
	}
	if cfg.LogLevel == "" {
		cfg.LogLevel = "info"
	}

	return cfg, nil
}
