import os

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("OPENROUTER_MODEL_PRIMARY", "test-primary")
os.environ.setdefault("OPENROUTER_MODEL_FALLBACK", "test-fallback")

import pytest

from triage.schemas import TriageResult


@pytest.mark.asyncio
async def test_text_run_returns_supplied_transcript(monkeypatch):
    import triage.run as run_module

    expected = TriageResult.model_validate({
        "issues": [{"type": "unsupported", "confidence": 1.0}],
        "actor": None,
        "jurisdictionState": None,
        "urgency": "general",
        "cards": {"whatMayBeHappening": {"text": "Other"}, "whatMayProtectYou": [], "whatYouCanDoNext": []},
    })

    async def understanding(**_):
        return object()
    async def retrieval(**_):
        return object()
    async def generation(**_):
        return object()
    monkeypatch.setattr(run_module, "understand", understanding)
    monkeypatch.setattr(run_module, "retrieve", retrieval)
    monkeypatch.setattr(run_module, "generate", generation)
    monkeypatch.setattr(run_module, "validate", lambda **_: expected.model_copy())

    result = await run_module.run(input_mode="text", text="My wages are unpaid", audio_bytes=None, language="en", user_context=None)
    assert result.transcript == "My wages are unpaid"
    assert result.issues == expected.issues


@pytest.mark.asyncio
async def test_voice_run_returns_stt_transcript(monkeypatch):
    import triage.run as run_module
    from triage.schemas import SttResult

    expected = TriageResult.model_validate({
        "issues": [{"type": "unsupported", "confidence": 1.0}],
        "actor": None,
        "jurisdictionState": None,
        "urgency": "general",
        "cards": {"whatMayBeHappening": {"text": "Other"}, "whatMayProtectYou": [], "whatYouCanDoNext": []},
    })
    monkeypatch.setattr(run_module, "transcribe", lambda *_: SttResult(text="अंतिम प्रतिलेख", language="hi", durationSeconds=1))
    async def stage(**_):
        return object()
    monkeypatch.setattr(run_module, "understand", stage)
    monkeypatch.setattr(run_module, "retrieve", stage)
    monkeypatch.setattr(run_module, "generate", stage)
    monkeypatch.setattr(run_module, "validate", lambda **_: expected.model_copy())

    result = await run_module.run(input_mode="voice", text=None, audio_bytes=b"audio", language="hi", user_context=None)
    assert result.transcript == "अंतिम प्रतिलेख"
    assert result.urgency == "general"
