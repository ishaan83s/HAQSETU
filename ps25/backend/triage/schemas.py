"""P2-only data contracts for the triage pipeline."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

IssueType = Literal[
    "wage_nonpayment", "wrongful_termination", "tenancy_eviction", "unsupported"
]
Urgency = Literal["general", "time_sensitive", "urgent"]


class IssueLabel(BaseModel):
    type: IssueType
    confidence: float = Field(ge=0.0, le=1.0)


class UnderstandingResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    actor: str | None = None
    what: str
    where: str | None = None
    when: str | None = None
    issues: list[IssueLabel] = Field(min_length=1, max_length=2)
    jurisdiction_state: Literal["Maharashtra"] | None = Field(
        default=None, alias="jurisdictionState"
    )
    urgency: Urgency

    @field_validator("what")
    @classmethod
    def non_empty_what(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("what must contain at least three characters")
        return value


class SttResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    text: str
    language: Literal["hi", "en"]
    duration_seconds: float = Field(ge=0.0, alias="durationSeconds")


class LegalSource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    title: str
    section: str | None = None
    jurisdiction_state: Literal["Maharashtra", "central"] | None = Field(
        default=None, alias="jurisdictionState"
    )
    source_url: str = Field(alias="sourceUrl")
    effective_date: date | None = Field(default=None, alias="effectiveDate")
    version_label: str | None = Field(default=None, alias="versionLabel")


class RetrievedChunk(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    source: LegalSource
    source_id: str = Field(alias="sourceId")
    passage: str
    score: float


class RetrievalResult(BaseModel):
    results: list[RetrievedChunk]


class GeneratedClaim(BaseModel):
    text: str
    source_id: str = Field(alias="sourceId")


class GenerationDraft(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    what_may_be_happening: dict[str, str] = Field(alias="whatMayBeHappening")
    what_may_protect_you: list[GeneratedClaim] = Field(alias="whatMayProtectYou")
    what_you_can_do_next: list[GeneratedClaim] = Field(alias="whatYouCanDoNext")


class ClaimWithSource(BaseModel):
    text: str
    source: LegalSource


class TriageCards(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    what_may_be_happening: dict[str, str] = Field(alias="whatMayBeHappening")
    what_may_protect_you: list[ClaimWithSource] = Field(alias="whatMayProtectYou")
    what_you_can_do_next: list[ClaimWithSource] = Field(alias="whatYouCanDoNext")


class TriageResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    transcript: str = ""
    issues: list[IssueLabel]
    actor: str | None = None
    jurisdiction_state: Literal["Maharashtra"] | None = Field(
        default=None, alias="jurisdictionState"
    )
    urgency: Urgency
    cards: TriageCards
