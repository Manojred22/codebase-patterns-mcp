package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"acme-platform-go/pkg/auth"
	"acme-platform-go/pkg/config"
	"acme-platform-go/pkg/telemetry"
)

func main() {
	cfg, err := config.LoadBaseConfig()
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	// Initialize Acme telemetry — MUST be done before any other initialization
	tp, err := telemetry.NewTracer(telemetry.AcmeTracerConfig{
		ServiceName: cfg.ServiceName,
		TeamLabel:   cfg.TeamLabel,
		CostCenter:  cfg.CostCenter,
		Environment: cfg.Environment,
		SampleRate:  0.1,
	})
	if err != nil {
		log.Fatalf("Failed to initialize tracer: %v", err)
	}
	defer telemetry.Shutdown(context.Background())
	_ = tp

	// Set up Acme auth middleware
	authMiddleware := auth.NewAuthMiddleware(auth.AcmeAuthConfig{
		RequiredScopes: []string{"read:data"},
		AllowInternal:  true,
	})

	mux := http.NewServeMux()
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		fmt.Fprintf(w, `{"status":"ok","service":"%s"}`, cfg.ServiceName)
	})

	server := &http.Server{
		Addr:    fmt.Sprintf(":%d", cfg.Port),
		Handler: authMiddleware(mux),
	}

	// Graceful shutdown
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		log.Printf("[%s] Starting on :%d (team=%s, env=%s)", cfg.ServiceName, cfg.Port, cfg.TeamLabel, cfg.Environment)
		if err := server.ListenAndServe(); err != http.ErrServerClosed {
			log.Fatalf("Server error: %v", err)
		}
	}()

	<-stop
	log.Println("Shutting down...")
	server.Shutdown(context.Background())
}
