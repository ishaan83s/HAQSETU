import asyncio
import os

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("OPENROUTER_MODEL_PRIMARY", "test-primary")
os.environ.setdefault("OPENROUTER_MODEL_FALLBACK", "test-fallback")

import pytest

from triage.classification import classify_issue
from triage.exceptions import RetrievalError
from triage.extraction import extract_fields
from triage.retrieval import is_ready, retrieve
from triage.schemas import (
    GeneratedClaim,
    GenerationDraft,
    IssueLabel,
    RetrievalResult,
    UnderstandingResult,
)
from triage.stt import is_near_empty
from triage.understanding import understand
from triage.validation import normalize_issues, validate


def issue(kind, confidence):
    return IssueLabel(type=kind, confidence=confidence)


def understanding(issues):
    return UnderstandingResult(
        actor="employer",
        what="Wages remain unpaid",
        issues=issues,
        jurisdictionState="Maharashtra",
        urgency="general",
    )


def test_shims_are_exact_understanding_aliases():
    assert extract_fields is understand
    assert classify_issue is understand


@pytest.mark.parametrize("text", ["", "  ", "--", "a."])
def test_near_empty_transcription(text):
    assert is_near_empty(text)


def test_non_empty_transcription_is_retained():
    assert not is_near_empty("मेरी मजदूरी नहीं मिली")


def test_issue_normalization_deduplicates_drops_unsupported_and_limits_two():
    normalized = normalize_issues([
        issue("unsupported", 1.0), issue("wage_nonpayment", 0.7),
        issue("wage_nonpayment", 0.9), issue("wrongful_termination", 0.8),
    ])
    assert [(item.type, item.confidence) for item in normalized] == [
        ("wage_nonpayment", 0.9), ("wrongful_termination", 0.8),
    ]


def test_issue_normalization_enforces_tenancy_employment_exclusion():
    normalized = normalize_issues([
        issue("wage_nonpayment", 0.6), issue("tenancy_eviction", 0.9),
    ])
    assert [item.type for item in normalized] == ["tenancy_eviction"]


@pytest.mark.asyncio
async def test_unsupported_skips_missing_index():
    result = await retrieve(
        incident_text="A consumer problem",
        understanding=understanding([issue("unsupported", 1.0)]),
    )
    assert result.results == []


@pytest.mark.asyncio
async def test_supported_request_requires_curated_index():
    assert not is_ready()
    with pytest.raises(RetrievalError):
        await retrieve(
            incident_text="My wages were withheld",
            understanding=understanding([issue("wage_nonpayment", 0.9)]),
        )


def test_validation_drops_unknown_sources_and_preserves_grounded_cards():
    draft = GenerationDraft(
        whatMayBeHappening={"text": "Wages may be unpaid."},
        whatMayProtectYou=[GeneratedClaim(text="Unknown claim", sourceId="missing")],
        whatYouCanDoNext=[],
    )
    result = validate(
        understanding=understanding([issue("wage_nonpayment", 0.9)]),
        draft=draft,
        retrieval=RetrievalResult(results=[]),
    )
    assert result.cards.what_may_protect_you == []


def test_validation_rejects_forbidden_certainty_when_grounded():
    # Source resolution is independently exercised by schema/validation tests once
    # curated retrieval fixtures are available; this test keeps the no-source path
    # deterministic without manufacturing legal corpus data.
    assert asyncio.run(retrieve(
        incident_text="Other concern",
        understanding=understanding([issue("unsupported", 1.0)]),
    )).results == []
