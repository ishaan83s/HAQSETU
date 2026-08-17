"""Incident service layer.

Implements:
- Request validation and audio decoding/validation (WAV/WebM, <=8MB, <=60s)
- UserContext loading (passing None if absent)
- Real in-process triage.run invocation
- Incident and TriageResult persistence (Incident service exclusive owner)
- Near-empty transcription handling (200 success envelope, 0 DB writes)
- Deterministic Evidence and Legal Aid composition
- Public response composition with confidence stripping
- GET /incidents/{id} with ownership verification (404 on foreign/missing)
"""

from __future__ import annotations

import base64
import binascii
import io
import struct
import uuid
import wave
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from common.exceptions import AppException, ErrorCode
from common.models import Incident, TriageResult, User, UserContext
from evidence.service import get_for_issues
from incident.schemas import (
    ClaimWithSource,
    EmptyTranscriptionResponse,
    IncidentRequest,
    IncidentResponse,
    LegalAidCard,
    PublicIssue,
    PublicTriageResult,
    TriageCards,
    UserContextDTO,
)
from legalaid.service import get_primary_for_state
from triage.exceptions import (
    GenerationError,
    RetrievalError,
    SttError,
    UnderstandingError,
)
from triage.run import run as triage_run


def _extract_webm_duration(audio_bytes: bytes) -> Optional[float]:
    """Attempt to extract duration in seconds from WebM/Matroska header."""
    try:
        header_chunk = audio_bytes[:4096]
        pos = header_chunk.find(b"\x44\x89")
        if pos != -1 and pos + 3 <= len(header_chunk):
            size_byte = header_chunk[pos + 2]
            if size_byte == 0x84 and pos + 7 <= len(header_chunk):
                raw_duration = struct.unpack(">f", header_chunk[pos + 3 : pos + 7])[0]
            elif size_byte == 0x88 and pos + 11 <= len(header_chunk):
                raw_duration = struct.unpack(">d", header_chunk[pos + 3 : pos + 11])[0]
            else:
                return None

            tc_pos = header_chunk.find(b"\x2a\xd7\xb1")
            timecode_scale = 1_000_000  # default 1ms in ns
            if tc_pos != -1 and tc_pos + 4 <= len(header_chunk):
                tc_size = header_chunk[tc_pos + 3] & 0x7F
                if tc_pos + 4 + tc_size <= len(header_chunk):
                    tc_bytes = header_chunk[tc_pos + 4 : tc_pos + 4 + tc_size]
                    timecode_scale = int.from_bytes(tc_bytes, byteorder="big")

            duration_secs = (raw_duration * timecode_scale) / 1e9
            return duration_secs
    except Exception:
        pass
    return None


def validate_and_decode_audio(audio_base64: str) -> bytes:
    """Validate and decode base64 audio payload (SSOT 03 §9.1).

    Constraints:
    - Base64 valid
    - Decoded payload <= 8 MB
    - Non-empty
    - Supported container: WAV or WebM/Opus
    - Duration <= 60 seconds
    """
    if not isinstance(audio_base64, str) or not audio_base64.strip():
        raise AppException(ErrorCode.INVALID_INPUT, "Audio base64 payload is empty.")

    try:
        audio_bytes = base64.b64decode(audio_base64.strip(), validate=True)
    except (binascii.Error, ValueError) as exc:
        raise AppException(ErrorCode.INVALID_INPUT, "Invalid base64 audio data.") from exc

    if len(audio_bytes) == 0:
        raise AppException(ErrorCode.INVALID_INPUT, "Decoded audio is empty.")

    if len(audio_bytes) > 8 * 1024 * 1024:
        raise AppException(ErrorCode.INVALID_INPUT, "Audio payload exceeds 8MB limit.")

    # Check magic bytes
    is_wav = len(audio_bytes) >= 12 and audio_bytes[:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE"
    is_webm = len(audio_bytes) >= 4 and audio_bytes[:4] == b"\x1a\x45\xdf\xa3"

    if not (is_wav or is_webm):
        raise AppException(
            ErrorCode.INVALID_INPUT,
            "Unsupported audio format. Only WAV and WebM/Opus are supported.",
        )

    # Validate duration if WAV
    if is_wav:
        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
                nframes = wf.getnframes()
                framerate = wf.getframerate()
                if framerate > 0:
                    duration = nframes / float(framerate)
                    if duration > 60.0:
                        raise AppException(
                            ErrorCode.INVALID_INPUT,
                            f"Audio duration ({duration:.1f}s) exceeds 60 second limit.",
                        )
        except AppException:
            raise
        except Exception:
            pass

    # Validate duration if WebM
    if is_webm:
        duration = _extract_webm_duration(audio_bytes)
        if duration is not None and duration > 60.0:
            raise AppException(
                ErrorCode.INVALID_INPUT,
                f"Audio duration ({duration:.1f}s) exceeds 60 second limit.",
            )

    return audio_bytes


def validate_incident_request(request: IncidentRequest) -> Tuple[Optional[str], Optional[str]]:
    """Validate request payload according to frozen rules."""
    has_text = request.text is not None
    has_audio = request.audio_base64 is not None

    if has_text == has_audio:
        raise AppException(
            ErrorCode.EMPTY_INCIDENT,
            "Exactly one of text or audioBase64 must be provided.",
        )

    if request.input_mode not in ("text", "voice"):
        raise AppException(
            ErrorCode.INVALID_INPUT,
            "inputMode must be 'text' or 'voice'.",
        )

    if request.language not in ("hi", "en"):
        raise AppException(
            ErrorCode.INVALID_INPUT,
            "language must be 'hi' or 'en'.",
        )

    if request.input_mode == "text":
        if not has_text or has_audio:
            raise AppException(
                ErrorCode.INVALID_INPUT,
                "inputMode 'text' requires text and forbids audioBase64.",
            )
        clean_text = request.text.strip()
        if not clean_text:
            raise AppException(
                ErrorCode.EMPTY_INCIDENT,
                "Incident text cannot be empty.",
            )
        return clean_text, None

    if request.input_mode == "voice":
        if not has_audio or has_text:
            raise AppException(
                ErrorCode.INVALID_INPUT,
                "inputMode 'voice' requires audioBase64 and forbids text.",
            )
        return None, request.audio_base64

    raise AppException(ErrorCode.INVALID_INPUT, "Invalid input payload.")


async def create_incident(
    db: AsyncSession,
    current_user: User,
    request: IncidentRequest,
) -> IncidentResponse | EmptyTranscriptionResponse:
    """Execute triage pipeline, persist incident & triage records, and return composed response."""
    clean_text, raw_audio = validate_incident_request(request)

    audio_bytes: Optional[bytes] = None
    if request.input_mode == "voice":
        assert raw_audio is not None
        audio_bytes = validate_and_decode_audio(raw_audio)
        clean_text = None

    # Load optional user context
    stmt = select(UserContext).where(UserContext.user_id == current_user.id)
    result = await db.execute(stmt)
    user_context_row = result.scalar_one_or_none()

    user_context_dto: Optional[UserContextDTO] = None
    if user_context_row is not None:
        user_context_dto = UserContextDTO(
            state=user_context_row.state,
            roleCategory=user_context_row.role_category,
            vulnerabilityTags=user_context_row.vulnerability_tags,
        )

    # Call triage pipeline
    try:
        triage_result = await triage_run(
            input_mode=request.input_mode,
            text=clean_text,
            audio_bytes=audio_bytes,
            language=request.language,
            user_context=user_context_dto,
        )
    except SttError as exc:
        if str(exc) == "Empty transcription" or "empty transcription" in str(exc).lower():
            return EmptyTranscriptionResponse(empty_transcription=True)
        raise AppException(ErrorCode.STT_FAILED) from exc
    except UnderstandingError as exc:
        raise AppException(ErrorCode.UNDERSTANDING_FAILED) from exc
    except RetrievalError as exc:
        raise AppException(ErrorCode.RETRIEVAL_UNAVAILABLE) from exc
    except GenerationError as exc:
        raise AppException(ErrorCode.GENERATION_FAILED) from exc
    except AppException:
        raise
    except Exception as exc:
        raise AppException(ErrorCode.TRIAGE_UNAVAILABLE) from exc

    # Persist Incident
    incident_id = uuid.uuid4()
    incident = Incident(
        id=incident_id,
        user_id=current_user.id,
        raw_input_text=triage_result.transcript if triage_result.transcript else (clean_text or ""),
        input_mode=request.input_mode,
        language=request.language,
    )
    db.add(incident)

    # Persist TriageResult with internal confidence
    issues_internal = [
        {"type": issue.type, "confidence": issue.confidence}
        for issue in triage_result.issues
    ]
    response_cards_db = triage_result.cards.model_dump(by_alias=True)

    db_triage = TriageResult(
        id=uuid.uuid4(),
        incident_id=incident_id,
        issues=issues_internal,
        actor=triage_result.actor,
        jurisdiction_state=triage_result.jurisdiction_state,
        urgency=triage_result.urgency,
        response_cards=response_cards_db,
    )
    db.add(db_triage)
    await db.commit()
    await db.refresh(incident)

    # Resolve deterministic Evidence and Legal Aid
    issue_types = [issue.type for issue in triage_result.issues]
    evidence_items = await get_for_issues(db, issue_types)
    contact = await get_primary_for_state(db, triage_result.jurisdiction_state)

    # Compose public response (strip confidence)
    public_issues = [PublicIssue(type=issue.type) for issue in triage_result.issues]

    protect_claims = [
        ClaimWithSource.model_validate(c.model_dump(by_alias=True))
        for c in triage_result.cards.what_may_protect_you
    ]
    next_claims = [
        ClaimWithSource.model_validate(c.model_dump(by_alias=True))
        for c in triage_result.cards.what_you_can_do_next
    ]

    cards = TriageCards(
        whatMayBeHappening=triage_result.cards.what_may_be_happening,
        whatMayProtectYou=protect_claims,
        evidenceToKeep=evidence_items,
        whatYouCanDoNext=next_claims,
        legalAid=LegalAidCard(
            name=contact.name,
            contactInfo=contact.contact_info,
        ),
    )

    public_triage = PublicTriageResult(
        issues=public_issues,
        actor=triage_result.actor,
        jurisdictionState=triage_result.jurisdiction_state,
        urgency=triage_result.urgency,
        cards=cards,
    )

    return IncidentResponse(
        incidentId=incident.id,
        triage=public_triage,
    )


async def get_incident_by_id(
    db: AsyncSession,
    current_user: User,
    incident_id: UUID,
) -> IncidentResponse:
    """Retrieve an incident by ID with ownership verification and compose public response."""
    stmt = (
        select(Incident)
        .options(selectinload(Incident.triage))
        .where(Incident.id == incident_id)
    )
    result = await db.execute(stmt)
    incident = result.scalar_one_or_none()

    if incident is None or incident.user_id != current_user.id:
        raise AppException(ErrorCode.INCIDENT_NOT_FOUND)

    if incident.triage is None:
        raise AppException(ErrorCode.INCIDENT_NOT_FOUND)

    triage_record = incident.triage

    # Extract issue types from stored issues list
    issue_types = []
    public_issues = []
    for item in triage_record.issues:
        if isinstance(item, dict) and "type" in item:
            issue_types.append(item["type"])
            public_issues.append(PublicIssue(type=item["type"]))

    # Resolve deterministic Evidence and Legal Aid
    evidence_items = await get_for_issues(db, issue_types)
    contact = await get_primary_for_state(db, triage_record.jurisdiction_state)

    raw_cards = triage_record.response_cards or {}

    protect_claims = [
        ClaimWithSource.model_validate(c)
        for c in (raw_cards.get("whatMayProtectYou") or raw_cards.get("what_may_protect_you", []))
    ]
    next_claims = [
        ClaimWithSource.model_validate(c)
        for c in (raw_cards.get("whatYouCanDoNext") or raw_cards.get("what_you_can_do_next", []))
    ]

    cards = TriageCards(
        whatMayBeHappening=raw_cards.get("whatMayBeHappening") or raw_cards.get("what_may_be_happening", {}),
        whatMayProtectYou=protect_claims,
        evidenceToKeep=evidence_items,
        whatYouCanDoNext=next_claims,
        legalAid=LegalAidCard(
            name=contact.name,
            contactInfo=contact.contact_info,
        ),
    )

    public_triage = PublicTriageResult(
        issues=public_issues,
        actor=triage_record.actor,
        jurisdictionState=triage_record.jurisdiction_state,
        urgency=triage_record.urgency,
        cards=cards,
    )

    return IncidentResponse(
        incidentId=incident.id,
        triage=public_triage,
    )


__all__ = [
    "validate_and_decode_audio",
    "validate_incident_request",
    "create_incident",
    "get_incident_by_id",
]
