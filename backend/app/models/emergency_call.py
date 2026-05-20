"""SQLAlchemy model for the MVP emergency call pipeline output."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.models.base import Base
from app.core.config import settings

# Use String(36) for SQLite, native UUID for PostgreSQL
if settings.USE_SQLITE:
    _UUIDType = String(36)
else:
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    _UUIDType = PG_UUID(as_uuid=True)


class EmergencyCall(Base):
    """Stores one processed emergency call with all pipeline outputs."""

    __tablename__ = "emergency_calls"

    # Primary key
    call_id: uuid.UUID = Column(
        _UUIDType,
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
    )

    # Optional caller identifier supplied by the caller or the phone system
    caller_id: str | None = Column(String(255), nullable=True, index=True)

    # Tenant scoping (nullable for backward compatibility with existing rows)
    tenant_id = Column(String(36), nullable=True, index=True)

    # STT / raw transcript
    transcript: str = Column(Text, nullable=False)

    # Pipeline outputs
    intent: str = Column(String(64), nullable=False, default="unknown")
    emotion: str = Column(String(64), nullable=False, default="neutral")
    severity: str = Column(String(16), nullable=False, default="low")
    responder: str = Column(String(64), nullable=False, default="general")

    # Timestamps
    created_at: datetime = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # End-to-end wall-clock latency in milliseconds
    latency_ms: int = Column(Integer, nullable=False, default=0)
