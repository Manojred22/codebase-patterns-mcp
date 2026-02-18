"""
Acme Database Repository — base class for all SQLAlchemy repositories.

Uses acme-standard connection to db.internal.acme.com with SSL required.
Acme standard: NEVER hard-delete, always soft-delete.
"""

from datetime import datetime
from typing import Generic, TypeVar, Optional, List

from sqlalchemy import create_engine, Column, DateTime, String, Boolean
from sqlalchemy.orm import Session, declarative_base

AcmeBase = declarative_base()

T = TypeVar("T")


class AcmeSoftDeleteMixin:
    """Mixin that adds soft-delete support. Acme standard: never hard-delete."""

    deleted_at = Column(DateTime, nullable=True, default=None)
    deleted_by = Column(String, nullable=True, default=None)


class AcmeRepository(Generic[T]):
    """Base repository with standard CRUD operations for Acme services.

    All database access MUST go through a repository.
    Direct SQL queries are NOT allowed.
    """

    def __init__(self, session: Session, model_class):
        self.session = session
        self.model_class = model_class

    def find_by_id(self, id: str) -> Optional[T]:
        """Find a record by ID, excluding soft-deleted records."""
        return (
            self.session.query(self.model_class)
            .filter(self.model_class.id == id)
            .filter(self.model_class.deleted_at.is_(None))
            .first()
        )

    def find_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Find all non-deleted records with pagination."""
        return (
            self.session.query(self.model_class)
            .filter(self.model_class.deleted_at.is_(None))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def soft_delete(self, id: str, deleted_by: str) -> bool:
        """Soft-delete a record. Acme standard: never hard-delete."""
        record = self.find_by_id(id)
        if record:
            record.deleted_at = datetime.utcnow()
            record.deleted_by = deleted_by
            self.session.commit()
            return True
        return False

    def save(self, entity: T) -> T:
        """Save or update an entity."""
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity


def create_acme_engine(database: str, team_label: str, cost_center: str):
    """Create an Acme-standard database engine.

    Connects to db.internal.acme.com with SSL required.
    """
    connection_string = f"postgresql://acme_svc:{database}@db.internal.acme.com:5432/{database}?sslmode=verify-full"
    return create_engine(
        connection_string,
        pool_size=25,
        max_overflow=10,
        pool_pre_ping=True,
        connect_args={"application_name": f"acme-{team_label}"},
    )
