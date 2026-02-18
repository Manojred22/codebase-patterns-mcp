package database

import (
	"context"
	"database/sql"
	"fmt"
	"time"
)

// AcmeDBConfig holds Acme-standard database configuration.
type AcmeDBConfig struct {
	Host        string // Default: "db.internal.acme.com"
	Port        int
	Database    string
	SSLMode     string // Acme requires "verify-full" in production
	MaxConns    int
	TeamLabel   string
	CostCenter  string
}

// Repository is the base Acme repository with standard CRUD operations.
type Repository[T any] struct {
	db        *sql.DB
	tableName string
	teamLabel string
}

// NewRepository creates an Acme-standard repository with connection pooling and tracing.
func NewRepository[T any](db *sql.DB, tableName, teamLabel string) *Repository[T] {
	return &Repository[T]{
		db:        db,
		tableName: tableName,
		teamLabel: teamLabel,
	}
}

// FindByID retrieves a record by ID with Acme-standard tracing.
func (r *Repository[T]) FindByID(ctx context.Context, id string) (*T, error) {
	query := fmt.Sprintf("SELECT * FROM %s WHERE id = $1 AND deleted_at IS NULL", r.tableName)

	row := r.db.QueryRowContext(ctx, query, id)
	var result T
	if err := row.Scan(&result); err != nil {
		if err == sql.ErrNoRows {
			return nil, nil
		}
		return nil, fmt.Errorf("acme/db: FindByID failed for %s: %w", r.tableName, err)
	}
	return &result, nil
}

// SoftDelete marks a record as deleted (Acme standard: never hard-delete).
func (r *Repository[T]) SoftDelete(ctx context.Context, id string) error {
	query := fmt.Sprintf("UPDATE %s SET deleted_at = $1 WHERE id = $2", r.tableName)
	_, err := r.db.ExecContext(ctx, query, time.Now(), id)
	if err != nil {
		return fmt.Errorf("acme/db: SoftDelete failed for %s: %w", r.tableName, err)
	}
	return nil
}

// ConnectDB creates an Acme-standard database connection.
func ConnectDB(cfg AcmeDBConfig) (*sql.DB, error) {
	if cfg.Host == "" {
		cfg.Host = "db.internal.acme.com"
	}
	if cfg.SSLMode == "" {
		cfg.SSLMode = "verify-full"
	}
	if cfg.MaxConns == 0 {
		cfg.MaxConns = 25
	}

	dsn := fmt.Sprintf(
		"host=%s port=%d dbname=%s sslmode=%s",
		cfg.Host, cfg.Port, cfg.Database, cfg.SSLMode,
	)

	db, err := sql.Open("postgres", dsn)
	if err != nil {
		return nil, fmt.Errorf("acme/db: connection failed: %w", err)
	}

	db.SetMaxOpenConns(cfg.MaxConns)
	db.SetMaxIdleConns(cfg.MaxConns / 2)
	db.SetConnMaxLifetime(5 * time.Minute)

	return db, nil
}
