"""Pydantic schemas for the Incident API and triage boundary."""

from __future__ import annotations

from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class IncidentRequest(BaseModel):
    """Request payload for POST /incidents."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    input_mode: Literal["text", "voice"] = Field(alias="inputMode")
    language: Literal["hi", "en"]
    text: str | None = None
    audio_base64: str | None = Field(default=None, alias="audioBase64")

    @model_validator(mode="after")
    def validate_input_representation(self) -> "IncidentRequest":
        """Enforce the frozen text/voice representation invariant."""

        has_text = self.text is not None
        has_audio = self.audio_base64 is not None

        if has_text == has_audio:
            raise ValueError(
                "Exactly one of text or audioBase64 must be provided."
            )

        if self.input_mode == "text" and not has_text:
            raise ValueError(
                "inputMode 'text' requires text and forbids audioBase64."
            )

        if self.input_mode == "voice" and not has_audio:
            raise ValueError(
                "inputMode 'voice' requires audioBase64 and forbids text."
            )

        return self


class UserContextDTO(BaseModel):
    """Optional user context passed from Incident to Triage."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    state: str | None = None
    role_category: str | None = Field(
        default=None,
        alias="roleCategory",
    )
    vulnerability_tags: list[str] | None = Field(
        default=None,
        alias="vulnerabilityTags",
    )


class LegalSource(BaseModel):
    """Public legal-source representation."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    title: str
    section: str | None = None
    jurisdiction_state: Literal["Maharashtra"] | None = Field(
        default=None,
        alias="jurisdictionState",
    )
    source_url: str = Field(alias="sourceUrl")
    effective_date: date | None = Field(
        default=None,
        alias="effectiveDate",
    )
    version_label: str | None = Field(
        default=None,
        alias="versionLabel",
    )


class IssueLabel(BaseModel):
    """Internal triage issue representation."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    type: str
    confidence: float


class PublicIssue(BaseModel):
    """Public issue representation.

    Confidence is intentionally excluded from the API contract.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    type: str


class ClaimWithSource(BaseModel):
    """Grounded triage claim with its legal source."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    text: str
    source: LegalSource


class TriageCards(BaseModel):
    """AI-generated cards plus Incident-service enrichments."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    what_may_be_happening: dict = Field(alias="whatMayBeHappening")
    what_may_protect_you: list[ClaimWithSource] = Field(
        alias="whatMayProtectYou"
    )
    evidence_to_keep: list[str] = Field(alias="evidenceToKeep")
    what_you_can_do_next: list[ClaimWithSource] = Field(
        alias="whatYouCanDoNext"
    )
    legal_aid: "LegalAidCard" = Field(alias="legalAid")


class LegalAidCard(BaseModel):
    """Single legal-aid contact embedded in an incident result."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    name: str
    contact_info: str = Field(alias="contactInfo")


class TriageResult(BaseModel):
    """Internal triage result before Incident persistence/composition."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    issues: list[IssueLabel]
    actor: str | None = None
    jurisdiction_state: Literal["Maharashtra"] | None = Field(
        default=None,
        alias="jurisdictionState",
    )
    urgency: Literal["general", "time_sensitive", "urgent"]
    cards: "TriageCards"


class IncidentResponse(BaseModel):
    """Public success payload for POST/GET /incidents."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    incident_id: UUID = Field(alias="incidentId")
    triage: "PublicTriageResult"


class PublicTriageResult(BaseModel):
    """Public triage representation.

    The internal issue confidence values are intentionally stripped before
    this schema is returned through the API boundary.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    issues: list[PublicIssue]
    actor: str | None = None
    jurisdiction_state: Literal["Maharashtra"] | None = Field(
        default=None,
        alias="jurisdictionState",
    )
    urgency: Literal["general", "time_sensitive", "urgent"]
    cards: "TriageCards"


class EmptyTranscriptionResponse(BaseModel):
    """Recoverable response for near-empty voice transcription."""

    empty_transcription: bool = Field(
        default=True,
        alias="emptyTranscription",
    )


TriageCards.model_rebuild()
TriageResult.model_rebuild()
IncidentResponse.model_rebuild()
PublicTriageResult.model_rebuild()


__all__ = [
    "ClaimWithSource",
    "EmptyTranscriptionResponse",
    "IncidentRequest",
    "IncidentResponse",
    "IssueLabel",
    "LegalAidCard",
    "LegalSource",
    "PublicIssue",
    "PublicTriageResult",
    "TriageCards",
    "TriageResult",
    "UserContextDTO",
]