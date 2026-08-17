"""SQLAlchemy models — frozen database schema (SSOT 02 §6)."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    TIMESTAMP,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, relationship

from common.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = Column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    phone_number: Mapped[str] = Column(
        String(15),
        unique=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    context: Mapped["UserContext"] = relationship(
        "UserContext",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    incidents: Mapped[list["Incident"]] = relationship(
        "Incident",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserContext(Base):
    __tablename__ = "user_context"

    id: Mapped[uuid.UUID] = Column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = Column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    state: Mapped[str | None] = Column(
        String(50),
        nullable=True,
    )
    role_category: Mapped[str | None] = Column(
        String(50),
        nullable=True,
    )
    vulnerability_tags: Mapped[list[str] | None] = Column(
        postgresql.ARRAY(Text),
        server_default=text("'{}'"),
        nullable=True,
    )
    updated_at: Mapped[datetime] = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="context",
    )


class Incident(Base):
    __tablename__ = "incidents"

    __table_args__ = (
        CheckConstraint(
            "input_mode IN ('voice', 'text')",
            name="chk_incidents_input_mode",
        ),
        CheckConstraint(
            "language IN ('hi', 'en')",
            name="chk_incidents_language",
        ),
    )

    id: Mapped[uuid.UUID] = Column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = Column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    raw_input_text: Mapped[str] = Column(
        Text,
        nullable=False,
    )
    input_mode: Mapped[str] = Column(
        String(10),
        nullable=False,
    )
    language: Mapped[str] = Column(
        String(5),
        nullable=False,
    )
    created_at: Mapped[datetime] = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    triage: Mapped["TriageResult"] = relationship(
        "TriageResult",
        back_populates="incident",
        uselist=False,
        cascade="all, delete-orphan",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="incidents",
    )


class TriageResult(Base):
    __tablename__ = "triage_results"

    __table_args__ = (
        CheckConstraint(
            "urgency IN ('general', 'time_sensitive', 'urgent')",
            name="chk_triage_results_urgency",
        ),
    )

    id: Mapped[uuid.UUID] = Column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    incident_id: Mapped[uuid.UUID] = Column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    issues: Mapped[dict] = Column(
        postgresql.JSONB,
        nullable=False,
    )
    actor: Mapped[str | None] = Column(
        String(100),
        nullable=True,
    )
    jurisdiction_state: Mapped[str | None] = Column(
        String(50),
        nullable=True,
    )
    urgency: Mapped[str] = Column(
        String(20),
        server_default=text("'general'"),
        nullable=False,
    )
    response_cards: Mapped[dict] = Column(
        postgresql.JSONB,
        nullable=False,
    )
    created_at: Mapped[datetime] = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    incident: Mapped["Incident"] = relationship(
        "Incident",
        back_populates="triage",
    )


class LegalSource(Base):
    __tablename__ = "legal_sources"

    __table_args__ = (
        CheckConstraint(
            "domain IN ('wage_employment', 'tenancy')",
            name="chk_legal_sources_domain",
        ),
        CheckConstraint(
            "jurisdiction_state IN ('Maharashtra', 'central')",
            name="chk_legal_sources_jurisdiction_state",
        ),
        Index(
            "idx_legal_sources_domain_jurisdiction",
            "domain",
            "jurisdiction_state",
        ),
    )

    id: Mapped[uuid.UUID] = Column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
    )
    title: Mapped[str] = Column(
        String(300),
        nullable=False,
    )
    section: Mapped[str | None] = Column(
        String(300),
        nullable=True,
    )
    domain: Mapped[str] = Column(
        String(30),
        nullable=False,
    )
    jurisdiction_state: Mapped[str] = Column(
        String(20),
        nullable=False,
    )
    source_url: Mapped[str] = Column(
        String(500),
        nullable=False,
    )
    effective_date: Mapped[date | None] = Column(
        Date,
        nullable=True,
    )
    version_label: Mapped[str | None] = Column(
        String(150),
        nullable=True,
    )


class EvidenceChecklist(Base):
    __tablename__ = "evidence_checklists"

    __table_args__ = (
        UniqueConstraint(
            "incident_type",
            name="uq_evidence_checklists_incident_type",
        ),
    )

    id: Mapped[uuid.UUID] = Column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    incident_type: Mapped[str] = Column(
        String(30),
        nullable=False,
    )
    items: Mapped[list[str]] = Column(
        postgresql.ARRAY(Text),
        server_default=text("'{}'"),
        nullable=False,
    )


class LegalAidContact(Base):
    __tablename__ = "legal_aid_contacts"

    __table_args__ = (
        Index(
            "idx_legal_aid_contacts_state_order",
            "state",
            "display_order",
        ),
    )

    id: Mapped[uuid.UUID] = Column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    state: Mapped[str] = Column(
        String(20),
        nullable=False,
    )
    name: Mapped[str] = Column(
        String(200),
        nullable=False,
    )
    contact_info: Mapped[str] = Column(
        String(300),
        nullable=False,
    )
    display_order: Mapped[int] = Column(
        Integer,
        server_default=text("0"),
        nullable=False,
    )


__all__ = [
    "User",
    "UserContext",
    "Incident",
    "TriageResult",
    "LegalSource",
    "EvidenceChecklist",
    "LegalAidContact",
]