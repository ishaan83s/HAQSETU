import os

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("OPENROUTER_MODEL_PRIMARY", "test-primary")
os.environ.setdefault("OPENROUTER_MODEL_FALLBACK", "test-fallback")

import pytest

from triage.classification import classify_issue
from triage.exceptions import RetrievalError
from triage.extraction import extract_fields
from triage.retrieval import _embedding, is_ready, retrieve
from triage.schemas import (
    GeneratedClaim,
    GenerationDraft,
    IssueLabel,
    LegalSource,
    RetrievalResult,
    RetrievedChunk,
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
async def test_supported_request_requires_curated_index(monkeypatch):
    _embedding()
    assert is_ready()
    result = await retrieve(
        incident_text="My wages were withheld",
        understanding=understanding([issue("wage_nonpayment", 0.9)]),
    )
    assert len(result.results) > 0

    monkeypatch.setattr("triage.retrieval.load_index", lambda: False)
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
    source = LegalSource(
        title="Curated source",
        section="1",
        jurisdictionState="central",
        sourceUrl="https://example.invalid/source",
    )
    retrieval = RetrievalResult(results=[RetrievedChunk(
        source=source,
        sourceId="source-1",
        passage="Curated passage",
        score=0.9,
    )])
    draft = GenerationDraft(
        whatMayBeHappening={"text": "Wages may be unpaid."},
        whatMayProtectYou=[GeneratedClaim(
            text="You have the right to unpaid wages.", sourceId="source-1"
        )],
        whatYouCanDoNext=[GeneratedClaim(
            text="The cited provision states this may require review.", sourceId="source-1"
        )],
    )
    result = validate(
        understanding=understanding([issue("wage_nonpayment", 0.9)]),
        draft=draft,
        retrieval=retrieval,
    )
    assert result.cards.what_may_protect_you == []
    resolved_source = result.cards.what_you_can_do_next[0].source
    assert resolved_source.jurisdiction_state is None
    assert resolved_source.title == source.title
    assert resolved_source.section == source.section
    assert resolved_source.source_url == source.source_url


def test_validation_retains_maharashtra_source_jurisdiction():
    source = LegalSource(
        title="Maharashtra source",
        section="2",
        jurisdictionState="Maharashtra",
        sourceUrl="https://example.invalid/maharashtra",
    )
    result = validate(
        understanding=understanding([issue("wage_nonpayment", 0.9)]),
        draft=GenerationDraft(
            whatMayBeHappening={"text": "Wages may be unpaid."},
            whatMayProtectYou=[GeneratedClaim(
                text="The cited provision states this may require review.",
                sourceId="source-1",
            )],
            whatYouCanDoNext=[],
        ),
        retrieval=RetrievalResult(results=[RetrievedChunk(
            source=source,
            sourceId="source-1",
            passage="Curated passage",
            score=0.9,
        )]),
    )
    assert result.cards.what_may_protect_you[0].source.jurisdiction_state == "Maharashtra"


def test_frozen_system_prompts_are_present():
    from triage.generation import SYSTEM_PROMPT as generation_prompt
    from triage.understanding import SYSTEM_PROMPT as understanding_prompt

    assert "You extract structured facts and classify the legal issue" in understanding_prompt
    assert "If nothing reaches 0.5" in understanding_prompt
    assert "You are the triage reasoning component of PS-25" in generation_prompt
    assert "Every sentence in \"whatMayProtectYou\"" in generation_prompt


@pytest.mark.asyncio
async def test_generate_zero_sources_returns_guardrail_without_calling_llm(monkeypatch):
    from triage.generation import generate

    llm_called = False

    async def fake_request(*_args, **_kwargs):
        nonlocal llm_called
        llm_called = True
        return {}

    monkeypatch.setattr("triage.generation._request", fake_request)

    draft = await generate(
        incident_text="Salary not paid",
        language="en",
        understanding=understanding([issue("wage_nonpayment", 0.9)]),
        retrieval=RetrievalResult(results=[]),
    )
    assert not llm_called
    assert draft.what_may_protect_you == []
    assert draft.what_may_be_happening["text"] == "Wages remain unpaid"


@pytest.mark.asyncio
async def test_generate_unsupported_issue_returns_guardrail_without_calling_llm(monkeypatch):
    from triage.generation import generate

    llm_called = False

    async def fake_request(*_args, **_kwargs):
        nonlocal llm_called
        llm_called = True
        return {}

    monkeypatch.setattr("triage.generation._request", fake_request)

    custom_understanding = UnderstandingResult(
        actor=None,
        what="Citizen describes an issue outside supported legal categories",
        issues=[issue("unsupported", 1.0)],
        jurisdictionState=None,
        urgency="general",
    )

    draft = await generate(
        incident_text="Random consumer refund issue",
        language="en",
        understanding=custom_understanding,
        retrieval=RetrievalResult(results=[]),
    )
    assert not llm_called
    assert draft.what_may_protect_you == []
    assert draft.what_may_be_happening["text"] == "Citizen describes an issue outside supported legal categories"


@pytest.mark.asyncio
async def test_generate_rejects_fabricated_source_id_and_raises_generation_error(monkeypatch):
    from triage.exceptions import GenerationError
    from triage.generation import generate

    call_count = 0

    async def fake_request(*_args, **_kwargs):
        nonlocal call_count
        call_count += 1
        return {
            "whatMayBeHappening": {"text": "Wages may be unpaid."},
            "whatMayProtectYou": [{"text": "Claim with fake source", "sourceId": "FAKE-999"}],
            "whatYouCanDoNext": [],
        }

    monkeypatch.setattr("triage.generation._request", fake_request)

    source = LegalSource(
        title="Valid Act",
        section="10",
        jurisdictionState="central",
        sourceUrl="https://example.invalid/act",
    )
    retrieval = RetrievalResult(results=[
        RetrievedChunk(source=source, sourceId="REAL-001", passage="Text", score=0.9)
    ])

    with pytest.raises(GenerationError, match="Grounded generation failed"):
        await generate(
            incident_text="Salary unpaid",
            language="en",
            understanding=understanding([issue("wage_nonpayment", 0.9)]),
            retrieval=retrieval,
        )

    assert call_count == 3  # Tried primary, primary+corrective, fallback


@pytest.mark.asyncio
async def test_generate_accepts_valid_grounded_source_id(monkeypatch):
    from triage.generation import generate

    async def fake_request(*_args, **_kwargs):
        return {
            "whatMayBeHappening": {"text": "Wages may be unpaid."},
            "whatMayProtectYou": [{"text": "Claim with real source", "sourceId": "REAL-001"}],
            "whatYouCanDoNext": [{"text": "Next action", "sourceId": "REAL-001"}],
        }

    monkeypatch.setattr("triage.generation._request", fake_request)

    source = LegalSource(
        title="Valid Act",
        section="10",
        jurisdictionState="central",
        sourceUrl="https://example.invalid/act",
    )
    retrieval = RetrievalResult(results=[
        RetrievedChunk(source=source, sourceId="REAL-001", passage="Text", score=0.9)
    ])

    draft = await generate(
        incident_text="Salary unpaid",
        language="en",
        understanding=understanding([issue("wage_nonpayment", 0.9)]),
        retrieval=retrieval,
    )
    assert len(draft.what_may_protect_you) == 1
    assert draft.what_may_protect_you[0].source_id == "REAL-001"

