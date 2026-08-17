"""Canonical async P2 triage orchestration."""
from __future__ import annotations

import asyncio
from typing import Literal

from triage.exceptions import SttError
from triage.generation import generate
from triage.retrieval import retrieve
from triage.schemas import TriageResult
from triage.stt import is_near_empty, transcribe
from triage.understanding import understand
from triage.validation import validate


async def run(*, input_mode: Literal["text", "voice"], text: str | None, audio_bytes: bytes | None, language: Literal["hi", "en"], user_context: object | None) -> TriageResult:
    """Run STT (where needed), understanding, retrieval, generation and validation."""
    if input_mode == "voice":
        if audio_bytes is None:
            raise SttError("Voice input requires audio bytes")
        try:
            stt_result = await asyncio.wait_for(asyncio.to_thread(transcribe, audio_bytes, language), timeout=45)
        except asyncio.TimeoutError as exc:
            raise SttError("Speech-to-text timed out") from exc
        incident_text = stt_result.text
    elif input_mode == "text":
        if text is None:
            raise ValueError("Text input requires text")
        incident_text = text.strip()
    else:
        raise ValueError("Unsupported input mode")
    if is_near_empty(incident_text):
        raise SttError("Empty transcription") if input_mode == "voice" else ValueError("Incident text is too short")
    understanding = await understand(incident_text=incident_text, language=language, user_context=user_context)
    retrieval = await retrieve(incident_text=incident_text, understanding=understanding)
    draft = await generate(incident_text=incident_text, language=language, understanding=understanding, retrieval=retrieval)
    result = validate(understanding=understanding, draft=draft, retrieval=retrieval)
    result.transcript = incident_text
    return result
