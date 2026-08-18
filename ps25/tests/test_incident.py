"""Tests for the PS-25 Incident module.

Covers:
- POST /incidents validation & representations (text, voice, mismatch, empty, oversized, format, duration)
- POST /incidents triage execution, context handoff, persistence, and confidence stripping
- POST /incidents recoverable empty transcription (200, 0 DB writes)
- POST /incidents triage failure mappings (502 for STT, Understanding, Retrieval, Generation, Unexpected)
- GET /incidents/{id} ownership enforcement (404 for missing/foreign user, never 403) and confidence stripping
"""

from __future__ import annotations

import base64
import io
import os
import struct
import uuid
import wave
from unittest.mock import AsyncMock, MagicMock

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("OPENROUTER_MODEL_PRIMARY", "test-primary")
os.environ.setdefault("OPENROUTER_MODEL_FALLBACK", "test-fallback")

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from common.exceptions import (
    AppException,
    ErrorCode,
    app_exception_handler,
    generic_exception_handler,
    validation_exception_handler,
)
from common.models import Incident, LegalAidContact, TriageResult, User, UserContext
from incident.router import router as incident_router
from incident.schemas import (
    EmptyTranscriptionResponse,
    IncidentRequest,
    IncidentResponse,
    PublicIssue,
    UserContextDTO,
)
from incident.service import (
    create_incident,
    get_incident_by_id,
    validate_and_decode_audio,
    validate_incident_request,
)
from triage.exceptions import (
    GenerationError,
    RetrievalError,
    SttError,
    UnderstandingError,
)
from triage.schemas import (
    ClaimWithSource as TriageClaimWithSource,
    IssueLabel as TriageIssueLabel,
    LegalSource as TriageLegalSource,
    TriageCards as TriageCardsInternal,
    TriageResult as TriageResultInternal,
)


def make_wav_bytes(duration_seconds: float = 1.0, sample_rate: int = 16000) -> bytes:
    """Generate minimal valid WAV audio bytes."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        nframes = int(duration_seconds * sample_rate)
        wf.writeframes(b"\x00\x00" * nframes)
    return buf.getvalue()


def make_webm_bytes(duration_seconds: float = 1.0) -> bytes:
    """Generate minimal valid WebM container bytes with Duration metadata."""
    ebml_header = b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01\x42\xf2\x81\x04\x42\xf3\x81\x08\x42\x82\x84webm"
    duration_ms = float(duration_seconds * 1000.0)
    duration_bytes = struct.pack(">f", duration_ms)
    info_chunk = b"\x15\x49\xa9\x66\x99\x2a\xd7\xb1\x83\x0f\x42\x40\x44\x89\x84" + duration_bytes
    return ebml_header + info_chunk + b"\x00" * 32


def make_webm_without_duration() -> bytes:
    """Generate minimal WebM container bytes missing the Duration metadata element."""
    ebml_header = b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01\x42\xf2\x81\x04\x42\xf3\x81\x08\x42\x82\x84webm"
    info_chunk = b"\x15\x49\xa9\x66\x99\x2a\xd7\xb1\x83\x0f\x42\x40"
    return ebml_header + info_chunk + b"\x00" * 32


def make_webm_with_corrupt_duration() -> bytes:
    """Generate minimal WebM container bytes with malformed/truncated duration element."""
    ebml_header = b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01\x42\xf2\x81\x04\x42\xf3\x81\x08\x42\x82\x84webm"
    info_chunk = b"\x15\x49\xa9\x66\x99\x2a\xd7\xb1\x83\x0f\x42\x40\x44\x89\x84\x00"
    return ebml_header + info_chunk


def make_mock_db() -> AsyncMock:
    """Create a mock database session with non-coroutine add method."""
    db = AsyncMock()
    db.add = MagicMock()
    return db


def mock_triage_result(transcript: str = "Unpaid wages for July") -> TriageResultInternal:
    """Construct a canonical internal TriageResult returned by triage.run()."""
    source = TriageLegalSource(
        title="Payment of Wages Act",
        section="Section 15",
        jurisdictionState="Maharashtra",
        sourceUrl="https://example.invalid/wages",
    )
    claim = TriageClaimWithSource(
        text="Wages must be paid by the 7th or 10th of each month.",
        source=source,
    )
    cards = TriageCardsInternal(
        whatMayBeHappening={"text": "Your wages appear to be delayed."},
        whatMayProtectYou=[claim],
        whatYouCanDoNext=[claim],
    )
    return TriageResultInternal(
        transcript=transcript,
        issues=[
            TriageIssueLabel(type="wage_nonpayment", confidence=0.92),
            TriageIssueLabel(type="wrongful_termination", confidence=0.81),
        ],
        actor="employer",
        jurisdictionState="Maharashtra",
        urgency="urgent",
        cards=cards,
    )


# ---------------------------------------------------------------------------
# Unit Tests: Request Validation & Audio Decoding
# ---------------------------------------------------------------------------


def test_validate_incident_request_text_success():
    req = IncidentRequest(
        inputMode="text",
        language="hi",
        text="मेरी मजदूरी नहीं मिली",
    )
    clean_text, raw_audio = validate_incident_request(req)
    assert clean_text == "मेरी मजदूरी नहीं मिली"
    assert raw_audio is None


def test_validate_incident_request_voice_success():
    wav_b64 = base64.b64encode(make_wav_bytes()).decode()
    req = IncidentRequest(
        inputMode="voice",
        language="en",
        audioBase64=wav_b64,
    )
    clean_text, raw_audio = validate_incident_request(req)
    assert clean_text is None
    assert raw_audio == wav_b64


def test_validate_incident_request_both_representations_empty_incident():
    req = IncidentRequest(
        inputMode="text",
        language="en",
        text="Sample text",
        audioBase64=base64.b64encode(b"RIFFdummyWAVE").decode(),
    )
    with pytest.raises(AppException) as exc_info:
        validate_incident_request(req)
    assert exc_info.value.code == ErrorCode.EMPTY_INCIDENT


def test_validate_incident_request_neither_representation_empty_incident():
    req = IncidentRequest(
        inputMode="text",
        language="en",
    )
    with pytest.raises(AppException) as exc_info:
        validate_incident_request(req)
    assert exc_info.value.code == ErrorCode.EMPTY_INCIDENT


def test_validate_incident_request_empty_text_empty_incident():
    req = IncidentRequest(
        inputMode="text",
        language="en",
        text="   ",
    )
    with pytest.raises(AppException) as exc_info:
        validate_incident_request(req)
    assert exc_info.value.code == ErrorCode.EMPTY_INCIDENT


def test_validate_incident_request_text_mode_with_audio_invalid_input():
    req = IncidentRequest(
        inputMode="text",
        language="en",
        audioBase64=base64.b64encode(make_wav_bytes()).decode(),
    )
    with pytest.raises(AppException) as exc_info:
        validate_incident_request(req)
    assert exc_info.value.code in (ErrorCode.EMPTY_INCIDENT, ErrorCode.INVALID_INPUT)


def test_validate_incident_request_voice_mode_with_text_invalid_input():
    req = IncidentRequest(
        inputMode="voice",
        language="en",
        text="Voice with text",
    )
    with pytest.raises(AppException) as exc_info:
        validate_incident_request(req)
    assert exc_info.value.code in (ErrorCode.EMPTY_INCIDENT, ErrorCode.INVALID_INPUT)


def test_validate_incident_request_invalid_language_invalid_input():
    req = IncidentRequest(
        inputMode="text",
        language="fr",
        text="Bonjour",
    )
    with pytest.raises(AppException) as exc_info:
        validate_incident_request(req)
    assert exc_info.value.code == ErrorCode.INVALID_INPUT


def test_validate_incident_request_invalid_input_mode_invalid_input():
    req = IncidentRequest(
        inputMode="carrier_pigeon",
        language="en",
        text="Hello",
    )
    with pytest.raises(AppException) as exc_info:
        validate_incident_request(req)
    assert exc_info.value.code == ErrorCode.INVALID_INPUT


def test_validate_and_decode_audio_valid_wav():
    wav_bytes = make_wav_bytes(duration_seconds=2.0)
    decoded = validate_and_decode_audio(base64.b64encode(wav_bytes).decode())
    assert decoded == wav_bytes


def test_validate_and_decode_audio_valid_webm():
    webm_bytes = make_webm_bytes(duration_seconds=5.0)
    decoded = validate_and_decode_audio(base64.b64encode(webm_bytes).decode())
    assert decoded == webm_bytes


def test_validate_and_decode_audio_invalid_base64():
    with pytest.raises(AppException) as exc_info:
        validate_and_decode_audio("!!!not-base-64!!!")
    assert exc_info.value.code == ErrorCode.INVALID_INPUT


def test_validate_and_decode_audio_unsupported_format():
    bad_bytes = b"MP3_HEADER_OR_UNKNOWN" * 5
    with pytest.raises(AppException) as exc_info:
        validate_and_decode_audio(base64.b64encode(bad_bytes).decode())
    assert exc_info.value.code == ErrorCode.INVALID_INPUT


def test_validate_and_decode_audio_oversized_payload():
    oversized = b"RIFF\x00\x00\x00\x00WAVE" + b"\x00" * (8 * 1024 * 1024 + 10)
    with pytest.raises(AppException) as exc_info:
        validate_and_decode_audio(base64.b64encode(oversized).decode())
    assert exc_info.value.code == ErrorCode.INVALID_INPUT


def test_validate_and_decode_audio_oversized_wav_duration():
    long_wav = make_wav_bytes(duration_seconds=65.0)
    with pytest.raises(AppException) as exc_info:
        validate_and_decode_audio(base64.b64encode(long_wav).decode())
    assert exc_info.value.code == ErrorCode.INVALID_INPUT


def test_validate_and_decode_audio_oversized_webm_duration():
    long_webm = make_webm_bytes(duration_seconds=65.0)
    with pytest.raises(AppException) as exc_info:
        validate_and_decode_audio(base64.b64encode(long_webm).decode())
    assert exc_info.value.code == ErrorCode.INVALID_INPUT


def test_validate_and_decode_audio_missing_webm_duration_fails_closed():
    """Test WebM with missing duration metadata is rejected (fail closed)."""
    webm_no_dur = make_webm_without_duration()
    with pytest.raises(AppException) as exc_info:
        validate_and_decode_audio(base64.b64encode(webm_no_dur).decode())
    assert exc_info.value.code == ErrorCode.INVALID_INPUT
    assert "duration" in exc_info.value.message.lower()


def test_validate_and_decode_audio_corrupt_webm_duration_fails_closed():
    """Test WebM with corrupt/truncated duration metadata is rejected (fail closed)."""
    webm_corrupt = make_webm_with_corrupt_duration()
    with pytest.raises(AppException) as exc_info:
        validate_and_decode_audio(base64.b64encode(webm_corrupt).decode())
    assert exc_info.value.code == ErrorCode.INVALID_INPUT
    assert "duration" in exc_info.value.message.lower()


# ---------------------------------------------------------------------------
# Unit / Service Tests: POST /incidents execution flow
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_incident_text_success(monkeypatch):
    """Test text incident creates Incident & TriageResult, calls triage.run, and composes response."""
    user = User(id=uuid.uuid4(), phone_number="+919876543210")
    req = IncidentRequest(
        inputMode="text",
        language="en",
        text="My employer withheld salary for 2 months",
    )

    triage_mock = mock_triage_result("My employer withheld salary for 2 months")
    run_called_with = {}

    async def fake_triage_run(**kwargs):
        run_called_with.update(kwargs)
        return triage_mock

    monkeypatch.setattr("incident.service.triage_run", fake_triage_run)

    async def fake_evidence(db, issue_types):
        return ["Pay slips", "Bank statement", "Appointment letter"]

    async def fake_legalaid(db, state):
        return LegalAidContact(
            id=uuid.uuid4(),
            state="Maharashtra",
            name="MSLSA",
            contact_info="1800-22-2324",
            display_order=1,
        )

    monkeypatch.setattr("incident.service.get_for_issues", fake_evidence)
    monkeypatch.setattr("incident.service.get_primary_for_state", fake_legalaid)

    db = make_mock_db()
    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = None
    db.execute.return_value = db_result

    response = await create_incident(db=db, current_user=user, request=req)

    assert isinstance(response, IncidentResponse)
    assert response.incident_id is not None
    assert response.triage.actor == "employer"
    assert response.triage.urgency == "urgent"
    assert response.triage.jurisdiction_state == "Maharashtra"
    assert response.triage.cards.evidence_to_keep == ["Pay slips", "Bank statement", "Appointment letter"]
    assert response.triage.cards.legal_aid.name == "MSLSA"
    assert response.triage.cards.legal_aid.contact_info == "1800-22-2324"

    # Verify public issues do NOT have confidence
    for pub_issue in response.triage.issues:
        assert isinstance(pub_issue, PublicIssue)
        assert hasattr(pub_issue, "type")
        assert not hasattr(pub_issue, "confidence") or pub_issue.model_dump().get("confidence") is None
        assert "confidence" not in pub_issue.model_dump()

    # Verify db.add was called twice (Incident and TriageResult)
    assert db.add.call_count == 2
    added_models = [call.args[0] for call in db.add.call_args_list]
    incident_added = next(m for m in added_models if isinstance(m, Incident))
    triage_added = next(m for m in added_models if isinstance(m, TriageResult))

    assert incident_added.raw_input_text == "My employer withheld salary for 2 months"
    assert incident_added.input_mode == "text"
    assert incident_added.language == "en"
    assert incident_added.user_id == user.id

    # Verify DB TriageResult contains internal confidence
    assert triage_added.incident_id == incident_added.id
    assert triage_added.issues[0]["confidence"] == 0.92
    assert triage_added.issues[1]["confidence"] == 0.81

    # Verify triage.run received clean_text and None for user_context
    assert run_called_with["input_mode"] == "text"
    assert run_called_with["text"] == "My employer withheld salary for 2 months"
    assert run_called_with["audio_bytes"] is None
    assert run_called_with["user_context"] is None


@pytest.mark.asyncio
async def test_post_incident_voice_success(monkeypatch):
    """Test voice incident decodes bytes, passes to triage.run, and persists canonical transcript."""
    user = User(id=uuid.uuid4(), phone_number="+919876543210")
    wav_bytes = make_wav_bytes(duration_seconds=3.0)
    req = IncidentRequest(
        inputMode="voice",
        language="hi",
        audioBase64=base64.b64encode(wav_bytes).decode(),
    )

    triage_mock = mock_triage_result("मेरी मजदूरी 2 महीने से नहीं मिली")
    run_called_with = {}

    async def fake_triage_run(**kwargs):
        run_called_with.update(kwargs)
        return triage_mock

    monkeypatch.setattr("incident.service.triage_run", fake_triage_run)
    monkeypatch.setattr("incident.service.get_for_issues", AsyncMock(return_value=["Dated photo"]))
    monkeypatch.setattr(
        "incident.service.get_primary_for_state",
        AsyncMock(return_value=LegalAidContact(state="Maharashtra", name="NALSA", contact_info="15100")),
    )

    db = make_mock_db()
    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = None
    db.execute.return_value = db_result

    response = await create_incident(db=db, current_user=user, request=req)

    assert isinstance(response, IncidentResponse)
    assert run_called_with["input_mode"] == "voice"
    assert run_called_with["text"] is None
    assert run_called_with["audio_bytes"] == wav_bytes

    added_models = [call.args[0] for call in db.add.call_args_list]
    incident_added = next(m for m in added_models if isinstance(m, Incident))
    assert incident_added.raw_input_text == "मेरी मजदूरी 2 महीने से नहीं मिली"


@pytest.mark.asyncio
async def test_post_incident_with_existing_user_context(monkeypatch):
    """Test existing UserContext row creates and passes UserContextDTO to triage.run."""
    user = User(id=uuid.uuid4(), phone_number="+919876543210")
    req = IncidentRequest(inputMode="text", language="en", text="Test incident")

    run_called_with = {}

    async def fake_triage_run(**kwargs):
        run_called_with.update(kwargs)
        return mock_triage_result()

    monkeypatch.setattr("incident.service.triage_run", fake_triage_run)
    monkeypatch.setattr("incident.service.get_for_issues", AsyncMock(return_value=[]))
    monkeypatch.setattr(
        "incident.service.get_primary_for_state",
        AsyncMock(return_value=LegalAidContact(state="Maharashtra", name="MSLSA", contact_info="1800")),
    )

    db = make_mock_db()
    ctx_row = UserContext(
        id=uuid.uuid4(),
        user_id=user.id,
        state="Maharashtra",
        role_category="factory_worker",
        vulnerability_tags=["unorganized_sector"],
    )
    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = ctx_row
    db.execute.return_value = db_result

    await create_incident(db=db, current_user=user, request=req)

    passed_ctx = run_called_with["user_context"]
    assert isinstance(passed_ctx, UserContextDTO)
    assert passed_ctx.state == "Maharashtra"
    assert passed_ctx.role_category == "factory_worker"
    assert passed_ctx.vulnerability_tags == ["unorganized_sector"]


@pytest.mark.asyncio
async def test_post_incident_near_empty_transcription_returns_200_no_db_write(monkeypatch):
    """Test voice STT near-empty transcription returns 200 recoverable response and zero DB writes."""
    user = User(id=uuid.uuid4(), phone_number="+919876543210")
    req = IncidentRequest(
        inputMode="voice",
        language="hi",
        audioBase64=base64.b64encode(make_wav_bytes()).decode(),
    )

    async def fake_triage_run(**kwargs):
        raise SttError("Empty transcription")

    monkeypatch.setattr("incident.service.triage_run", fake_triage_run)

    db = make_mock_db()
    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = None
    db.execute.return_value = db_result

    response = await create_incident(db=db, current_user=user, request=req)

    assert isinstance(response, EmptyTranscriptionResponse)
    assert response.empty_transcription is True
    assert db.add.call_count == 0
    assert db.commit.call_count == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "triage_exception,expected_code",
    [
        (SttError("Whisper hardware crashed"), ErrorCode.STT_FAILED),
        (UnderstandingError("LLM schema failed"), ErrorCode.UNDERSTANDING_FAILED),
        (RetrievalError("FAISS index unavailable"), ErrorCode.RETRIEVAL_UNAVAILABLE),
        (GenerationError("Ungrounded hallucination"), ErrorCode.GENERATION_FAILED),
        (RuntimeError("Unexpected connection drop"), ErrorCode.TRIAGE_UNAVAILABLE),
    ],
)
async def test_post_incident_triage_exceptions_mapped_to_502_no_db_writes(
    monkeypatch, triage_exception, expected_code
):
    """Test all triage failure exceptions map to 502 with corresponding ErrorCode and zero DB writes."""
    user = User(id=uuid.uuid4(), phone_number="+919876543210")
    req = IncidentRequest(inputMode="text", language="en", text="Valid incident text")

    async def fake_triage_run(**kwargs):
        raise triage_exception

    monkeypatch.setattr("incident.service.triage_run", fake_triage_run)

    db = make_mock_db()
    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = None
    db.execute.return_value = db_result

    with pytest.raises(AppException) as exc_info:
        await create_incident(db=db, current_user=user, request=req)

    assert exc_info.value.code == expected_code
    assert exc_info.value.status_code == 502
    assert db.add.call_count == 0
    assert db.commit.call_count == 0


# ---------------------------------------------------------------------------
# Unit / Service Tests: GET /incidents/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_incident_own_incident_success(monkeypatch):
    """Test retrieving own incident returns public shape with confidence stripped."""
    user = User(id=uuid.uuid4(), phone_number="+919876543210")
    incident_id = uuid.uuid4()

    db_triage = TriageResult(
        id=uuid.uuid4(),
        incident_id=incident_id,
        issues=[
            {"type": "wage_nonpayment", "confidence": 0.95},
            {"type": "wrongful_termination", "confidence": 0.75},
        ],
        actor="employer",
        jurisdiction_state="Maharashtra",
        urgency="general",
        response_cards={
            "whatMayBeHappening": {"text": "Wages unpaid"},
            "whatMayProtectYou": [
                {
                    "text": "Protected by Section 15",
                    "source": {
                        "title": "Payment of Wages",
                        "section": "15",
                        "jurisdictionState": "Maharashtra",
                        "sourceUrl": "https://example.invalid",
                    },
                }
            ],
            "whatYouCanDoNext": [],
        },
    )

    incident = Incident(
        id=incident_id,
        user_id=user.id,
        raw_input_text="My wages were withheld",
        input_mode="text",
        language="en",
    )
    incident.triage = db_triage

    monkeypatch.setattr("incident.service.get_for_issues", AsyncMock(return_value=["Pay slips"]))
    monkeypatch.setattr(
        "incident.service.get_primary_for_state",
        AsyncMock(return_value=LegalAidContact(state="Maharashtra", name="MSLSA", contact_info="1800-22-2324")),
    )

    db = make_mock_db()
    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = incident
    db.execute.return_value = db_result

    response = await get_incident_by_id(db=db, current_user=user, incident_id=incident_id)

    assert isinstance(response, IncidentResponse)
    assert response.incident_id == incident_id
    assert response.triage.actor == "employer"
    assert response.triage.urgency == "general"
    assert response.triage.cards.evidence_to_keep == ["Pay slips"]
    assert response.triage.cards.legal_aid.name == "MSLSA"

    for pub_issue in response.triage.issues:
        assert isinstance(pub_issue, PublicIssue)
        assert "confidence" not in pub_issue.model_dump()


@pytest.mark.asyncio
async def test_get_incident_nonexistent_returns_404():
    """Test nonexistent incident returns 404 INCIDENT_NOT_FOUND."""
    user = User(id=uuid.uuid4(), phone_number="+919876543210")
    db = make_mock_db()
    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = None
    db.execute.return_value = db_result

    with pytest.raises(AppException) as exc_info:
        await get_incident_by_id(db=db, current_user=user, incident_id=uuid.uuid4())

    assert exc_info.value.code == ErrorCode.INCIDENT_NOT_FOUND
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_incident_foreign_user_returns_404_never_403():
    """Test accessing another user's incident returns 404 (NEVER 403)."""
    user_a = User(id=uuid.uuid4(), phone_number="+919876543210")
    user_b_id = uuid.uuid4()
    incident_id = uuid.uuid4()

    incident = Incident(
        id=incident_id,
        user_id=user_b_id,
        raw_input_text="Secret incident",
        input_mode="text",
        language="en",
    )

    db = make_mock_db()
    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = incident
    db.execute.return_value = db_result

    with pytest.raises(AppException) as exc_info:
        await get_incident_by_id(db=db, current_user=user_a, incident_id=incident_id)

    assert exc_info.value.code == ErrorCode.INCIDENT_NOT_FOUND
    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Integration Tests: FastAPI TestClient with Router
# ---------------------------------------------------------------------------


def create_test_app(current_user: User, db_session: AsyncMock) -> FastAPI:
    """Create a FastAPI application with incident router and exception handlers."""
    app = FastAPI()
    app.include_router(incident_router)
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    from auth.router import get_current_user
    from common.db import get_async_session

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_async_session] = lambda: db_session
    return app


def test_api_post_incident_text_success(monkeypatch):
    """Test POST /incidents returns HTTP 201 with success envelope."""
    user = User(id=uuid.uuid4(), phone_number="+919876543210")
    db = make_mock_db()
    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = None
    db.execute.return_value = db_result

    triage_mock = mock_triage_result("Wages unpaid")
    monkeypatch.setattr("incident.service.triage_run", AsyncMock(return_value=triage_mock))
    monkeypatch.setattr("incident.service.get_for_issues", AsyncMock(return_value=["Bank statement"]))
    monkeypatch.setattr(
        "incident.service.get_primary_for_state",
        AsyncMock(return_value=LegalAidContact(state="Maharashtra", name="MSLSA", contact_info="1800")),
    )

    app = create_test_app(user, db)
    client = TestClient(app)

    response = client.post(
        "/incidents",
        json={"inputMode": "text", "language": "en", "text": "My salary was delayed"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    assert "incidentId" in body["data"]
    assert body["data"]["triage"]["actor"] == "employer"
    for issue_item in body["data"]["triage"]["issues"]:
        assert "confidence" not in issue_item


def test_api_post_incident_voice_success(monkeypatch):
    """Test POST /incidents returns HTTP 201 for voice input."""
    user = User(id=uuid.uuid4(), phone_number="+919876543210")
    db = make_mock_db()
    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = None
    db.execute.return_value = db_result

    triage_mock = mock_triage_result("मेरी मजदूरी 2 महीने से नहीं मिली")
    monkeypatch.setattr("incident.service.triage_run", AsyncMock(return_value=triage_mock))
    monkeypatch.setattr("incident.service.get_for_issues", AsyncMock(return_value=["Bank statement"]))
    monkeypatch.setattr(
        "incident.service.get_primary_for_state",
        AsyncMock(return_value=LegalAidContact(state="Maharashtra", name="MSLSA", contact_info="1800")),
    )

    app = create_test_app(user, db)
    client = TestClient(app)

    wav_b64 = base64.b64encode(make_wav_bytes(duration_seconds=2.0)).decode()
    response = client.post(
        "/incidents",
        json={"inputMode": "voice", "language": "hi", "audioBase64": wav_b64},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    assert "incidentId" in body["data"]


def test_api_post_incident_empty_transcription_200(monkeypatch):
    """Test POST /incidents with voice near-empty STT returns HTTP 200 with emptyTranscription=True."""
    user = User(id=uuid.uuid4(), phone_number="+919876543210")
    db = make_mock_db()
    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = None
    db.execute.return_value = db_result

    async def fake_triage_run(**_):
        raise SttError("Empty transcription")

    monkeypatch.setattr("incident.service.triage_run", fake_triage_run)

    app = create_test_app(user, db)
    client = TestClient(app)

    wav_b64 = base64.b64encode(make_wav_bytes()).decode()
    response = client.post(
        "/incidents",
        json={"inputMode": "voice", "language": "hi", "audioBase64": wav_b64},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] == {"emptyTranscription": True}
    assert body["error"] is None


def test_api_post_incident_validation_failure_empty_incident():
    """Test POST /incidents with both representations returns 422 EMPTY_INCIDENT."""
    user = User(id=uuid.uuid4(), phone_number="+919876543210")
    db = make_mock_db()
    app = create_test_app(user, db)
    client = TestClient(app)

    response = client.post(
        "/incidents",
        json={"inputMode": "text", "language": "en", "text": "Hello", "audioBase64": "RIFF"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "EMPTY_INCIDENT"


def test_api_post_incident_voice_missing_duration_fails_closed():
    """Test POST /incidents with WebM missing duration returns HTTP 422 with INVALID_INPUT."""
    user = User(id=uuid.uuid4(), phone_number="+919876543210")
    db = make_mock_db()
    app = create_test_app(user, db)
    client = TestClient(app)

    webm_no_dur = make_webm_without_duration()
    response = client.post(
        "/incidents",
        json={
            "inputMode": "voice",
            "language": "hi",
            "audioBase64": base64.b64encode(webm_no_dur).decode(),
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"]["code"] == "INVALID_INPUT"
    assert "duration" in body["error"]["message"].lower()


def test_api_post_incident_request_validation_missing_field_400():
    """Test POST /incidents with missing required schema field returns HTTP 400 INVALID_INPUT in envelope."""
    user = User(id=uuid.uuid4(), phone_number="+919876543210")
    db = make_mock_db()
    app = create_test_app(user, db)
    client = TestClient(app)

    # Missing required field 'inputMode'
    response = client.post(
        "/incidents",
        json={"language": "en", "text": "Missing input mode"},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"]["code"] == "INVALID_INPUT"
    assert "inputMode" in body["error"]["message"]


def test_api_post_incident_request_validation_forbidden_extra_field_400():
    """Test POST /incidents with forbidden extra field returns HTTP 400 INVALID_INPUT in envelope."""
    user = User(id=uuid.uuid4(), phone_number="+919876543210")
    db = make_mock_db()
    app = create_test_app(user, db)
    client = TestClient(app)

    # 'extraField' is forbidden by IncidentRequest ConfigDict(extra="forbid")
    response = client.post(
        "/incidents",
        json={
            "inputMode": "text",
            "language": "en",
            "text": "Valid text",
            "extraField": "disallowed",
        },
    )

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"]["code"] == "INVALID_INPUT"
    assert "extraField" in body["error"]["message"]


def test_api_main_app_request_validation_error_400():
    """Test global main app RequestValidationError returns HTTP 400 with canonical INVALID_INPUT envelope."""
    from main import app
    from auth.router import get_current_user
    from common.db import get_async_session

    user = User(id=uuid.uuid4(), phone_number="+919876543210")
    db = make_mock_db()

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_async_session] = lambda: db

    client = TestClient(app)

    # Missing required field 'inputMode' on main app POST /incidents
    response = client.post(
        "/incidents",
        json={"language": "en", "text": "Testing main app validation handler"},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"]["code"] == "INVALID_INPUT"
    assert "inputMode" in body["error"]["message"]


def test_api_get_incident_success(monkeypatch):
    """Test GET /incidents/{id} returns HTTP 200 for owned incident."""
    user = User(id=uuid.uuid4(), phone_number="+919876543210")
    incident_id = uuid.uuid4()

    db_triage = TriageResult(
        id=uuid.uuid4(),
        incident_id=incident_id,
        issues=[{"type": "wage_nonpayment", "confidence": 0.9}],
        actor="employer",
        jurisdiction_state="Maharashtra",
        urgency="general",
        response_cards={
            "whatMayBeHappening": {"text": "Wages unpaid"},
            "whatMayProtectYou": [],
            "whatYouCanDoNext": [],
        },
    )
    incident = Incident(
        id=incident_id,
        user_id=user.id,
        raw_input_text="My wages",
        input_mode="text",
        language="en",
    )
    incident.triage = db_triage

    monkeypatch.setattr("incident.service.get_for_issues", AsyncMock(return_value=["Pay slips"]))
    monkeypatch.setattr(
        "incident.service.get_primary_for_state",
        AsyncMock(return_value=LegalAidContact(state="Maharashtra", name="MSLSA", contact_info="1800")),
    )

    db = make_mock_db()
    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = incident
    db.execute.return_value = db_result

    app = create_test_app(user, db)
    client = TestClient(app)

    response = client.get(f"/incidents/{incident_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["incidentId"] == str(incident_id)


def test_api_get_incident_foreign_user_404():
    """Test GET /incidents/{id} returns 404 for incident owned by another user."""
    user_a = User(id=uuid.uuid4(), phone_number="+919876543210")
    user_b_id = uuid.uuid4()
    incident_id = uuid.uuid4()

    incident = Incident(
        id=incident_id,
        user_id=user_b_id,
        raw_input_text="Foreign incident",
        input_mode="text",
        language="en",
    )

    db = make_mock_db()
    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = incident
    db.execute.return_value = db_result

    app = create_test_app(user_a, db)
    client = TestClient(app)

    response = client.get(f"/incidents/{incident_id}")

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "INCIDENT_NOT_FOUND"


def test_api_health_ready_200(monkeypatch):
    """Test GET /health returns 200 when retrieval index is ready."""
    from main import app

    monkeypatch.setattr("main.is_ready", lambda: True)
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] == {"status": "ok"}
    assert body["error"] is None


def test_api_health_unavailable_503(monkeypatch):
    """Test GET /health returns 503 RETRIEVAL_UNAVAILABLE when index is not ready."""
    from main import app

    monkeypatch.setattr("main.is_ready", lambda: False)
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 503
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"]["code"] == "RETRIEVAL_UNAVAILABLE"


def test_api_put_user_context_success():
    """Test PUT /users/context saves user context and returns 200."""
    from main import app
    from auth.router import get_current_user
    from common.db import get_async_session

    user = User(id=uuid.uuid4(), phone_number="+919876543210")
    db = make_mock_db()
    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = None
    db.execute.return_value = db_result

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_async_session] = lambda: db

    client = TestClient(app)

    response = client.put(
        "/users/context",
        json={
            "state": "Maharashtra",
            "roleCategory": "worker",
            "vulnerabilityTags": ["gig_worker"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] == {"saved": True}
    assert body["error"] is None
    assert db.add.call_count == 1
    assert db.commit.call_count == 1
