"""Blocking faster-whisper boundary used by ``triage.run``."""
from __future__ import annotations

import re
from typing import Literal

from triage.exceptions import SttError
from triage.schemas import SttResult

_model = None


def load_model():
    """Load the single CPU/int8 Whisper model instance on first use."""
    global _model
    if _model is None:
        try:
            from faster_whisper import WhisperModel

            _model = WhisperModel("small", device="cpu", compute_type="int8")
        except Exception as exc:  # model/download/decode provider boundary
            raise SttError("Speech-to-text is unavailable") from exc
    return _model


def transcribe(audio_bytes: bytes, language: Literal["hi", "en"]) -> SttResult:
    """Transcribe one audio payload with explicit language only."""
    if language not in {"hi", "en"}:
        raise SttError("Unsupported transcription language")
    if not audio_bytes:
        raise SttError("Audio input is empty")
    try:
        segments, info = load_model().transcribe(
            audio_bytes,
            language=language,
            beam_size=5,
            temperature=0.0,
            vad_filter=True,
        )
        text = " ".join(segment.text.strip() for segment in segments).strip()
        return SttResult(
            text=text,
            language=language,
            durationSeconds=float(getattr(info, "duration", 0.0)),
        )
    except SttError:
        raise
    except Exception as exc:
        raise SttError("Speech-to-text failed") from exc


def is_near_empty(text: str) -> bool:
    stripped = text.strip()
    return len(stripped) < 3 or bool(re.fullmatch(r"[\W_]*", stripped))
