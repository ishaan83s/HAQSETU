"""SQLAlchemy models — frozen database schema (SSOT 02 §6).

All tables defined here are registered on the Base metadata and created
via SQLAlchemy.metadata.create_all() at startup (SSOT 02 §6.1, SSOT 09 §34.3).

Frozen DDL decisions (SSOT 02 §6.10):
  - PostgreSQL TIMESTAMPTZ for all timestamps (with server_default=func.now())
  - UUID via gen_random_uuid() from pgcrypto extension
  - Varchar lengths per column (no unbounded varchars)
  - FK ON DELETE CASCADE for user\u2192context and incident\u2192triage_results
  - FK ON DELETE SET NULL for incidents\u2192users (preserve incidents if user deleted)
  - Unique constraints on phone_number, user_context.user_id, evidence_checklists.incident_type
  - CHECK constraints for input_mode, language, urgency (enum strategy)
  - JSONB columns for issues and response_cards (no DB-level schema validation \u2014 Pydantic validates)
  - TEXT[] columns with DEFAULT '{}' for vulnerability_tags and evidence items

No extra tables (SSOT 02 §6.9: document_drafts is FUTURE only).
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    String,
    Text,
    TIMESTAMP,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship, mapped, Mapped




# ────────────────────────────────────────────────────────────────────────
# USERS
# SSOT 02 §6.2: id (UUID PK), phone_number (varchar, UNIQUE), created_at (timestamp)
# ────────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id: Mapped[postgresql.UUID] = Column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
                server_default=text("gen_random_uuid()"),
        nullable=False,
    )
    phone_number: Mapped[str] = Column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )
    created_at: Mapped[str] = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
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


# ────────────────────────────────────────────────────────────────────────
# USER_CONTEXT  (SSOT 02 §6.3)
# ────────────────────────────────────────────────────────────────────────
class UserContext(Base):
    __tablename__ = "user_context"

    id: Mapped[postgresql.UUID] = Column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False,
    )
    user_id: Mapped[postgresql.UUID] = Column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    state: Mapped[str | None] = Column(String(50), nullable=True)
    role_category: Mapped[str | None] = Column(String(50), nullable=True)
    vulnerability_tags: Mapped[list[str] | None] = Column(
        postgresql.ARRAY(Text),
        server_default=text("'{}'"),
        nullable=True,
    )
    updated_at: Mapped[str] = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
        onupdate=func.now(),
    )

        user: Mapped["User"] = relationship("User", back_populates="context")


# ────────────────────────────────────────────────────────────────────────
# INCIDENTS  (SSOT 02 §6.4)
# ────────────────────────────────────────────────────────────────────────
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

    id: Mapped[postgresql.UUID] = Column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False,
    )
    user_id: Mapped[postgresql.UUID | None] = Column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    raw_input_text: Mapped[str | None] = Column(Text, nullable=True)
    input_mode: Mapped[str] = Column(String(10), nullable=False)
    language: Mapped[str] = Column(String(5), nullable=False)
    created_at: Mapped[str] = Column(
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
        user: Mapped["User"] = relationship("User", back_populates="incidents")


# ────────────────────────────────────────────────────────────────────────
# TRIAGE_RESULTS  (SSOT 02 §6.5)
# ────────────────────────────────────────────────────────────────────────
class TriageResult(Base):
    __tablename__ = "triage_results"

    __table_args__ = (
        CheckConstraint(
            "urgency IN ('general', 'time_sensitive', 'urgent')",
            name="chk_triage_results_urgency",
        ),
    )

    id: Mapped[postgresql.UUID] = Column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False,
    )
    incident_id: Mapped[postgresql.UUID] = Column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    issues: Mapped[dict] = Column(postgresql.JSONB, nullable=False)
    actor: Mapped[str | None] = Column(String(100), nullable=True)
    jurisdiction_state: Mapped[str | None] = Column(String(50), nullable=True)
    urgency: Mapped[str] = Column(String(20), nullable=False)
    response_cards: Mapped[dict] = Column(postgresql.JSONB, nullable=False)
    created_at: Mapped[str] = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

        incident: Mapped["Incident"] = relationship("Incident", back_populates="triage")


# ────────────────────────────────────────────────────────────────────────
# LEGAL_SOURCES  (SSOT 02 §6.6)
# ────────────────────────────────────────────────────────────────────────
class LegalSource(Base):
    __tablename__ = "legal_sources"

    __table_args__ = (
        Index("idx_legal_sources_domain", "domain"),
        Index("idx_legal_sources_jurisdiction", "jurisdiction_state"),
        Index("idx_legal_sources_domain_jurisdiction", "domain", "jurisdiction_state"),
    )

    id: Mapped[postgresql.UUID] = Column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False,
    )
    title: Mapped[str] = Column(String(255), nullable=False)
    section: Mapped[str | None] = Column(String(100), nullable=True)
    domain: Mapped[str | None] = Column(String(50), nullable=True)
    jurisdiction_state: Mapped[str | None] = Column(String(50), nullable=True)
    source_url: Mapped[str] = Column(String(500), nullable=False)
    effective_date: Mapped[date | None] = Column(Date, nullable=True)
    version_label: Mapped[str | None] = Column(String(50), nullable=True)


# ────────────────────────────────────────────────────────────────────────
# EVIDENCE_CHECKLISTS  (SSOT 02 §6.7)
# ────────────────────────────────────────────────────────────────────────
class EvidenceChecklist(Base):
    __tablename__ = "evidence_checklists"

    __table_args__ = (
                UniqueConstraint("incident_type", name="uq_evidence_checklists_incident_type"),
    )

    id: Mapped[postgresql.UUID] = Column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False,
    )
    incident_type: Mapped[str] = Column(String(100), nullable=False, index=True)
        items: Mapped[list[str]] = Column(postgresql.ARRAY(Text), nullable=False)


# ────────────────────────────────────────────────────────────────────────
# LEGAL_AID_CONTACTS  (SSOT 02 §6.8)
# ────────────────────────────────────────────────────────────────────────
class LegalAidContact(Base):
    __tablename__ = "legal_aid_contacts"

    __table_args__ = (
        Index("idx_legal_aid_contacts_state", "state"),
    )

    id: Mapped[postgresql.UUID] = Column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False,
    )
    state: Mapped[str] = Column(String(50), nullable=False, index=True)
    name: Mapped[str] = Column(String(100), nullable=False)
    contact_info: Mapped[str] = Column(String(255), nullable=False)


__all__ = [
    "User",
    "UserContext",
    "Incident",
    "TriageResult",
    "LegalSource",
    "EvidenceChecklist",
    "LegalAidContact",
]