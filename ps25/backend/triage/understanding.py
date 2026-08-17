"""The single OpenRouter extraction-and-classification call."""
from __future__ import annotations

import asyncio
import json
from typing import Literal

import httpx

from common.config import settings
from triage.exceptions import UnderstandingError
from triage.schemas import UnderstandingResult

SYSTEM_PROMPT = """You extract structured facts and classify a citizen's incident. Output only JSON with actor, what, where, when, issues, jurisdictionState, urgency. Supported issues: wage_nonpayment, wrongful_termination, tenancy_eviction, unsupported. Choose one or two supported issues; unsupported is alone. Confidence is 0.0-1.0. Maharashtra is the only permitted jurisdictionState; otherwise null. Urgency: urgent for eviction/lockout/threat, time_sensitive for deadlines/notices or termination with wage issue, else general. Do not provide legal advice."""


def _context_value(user_context: object | None, name: str) -> object:
    if user_context is None:
        return None
    return getattr(user_context, name, None)


async def _call(model: str, prompt: str) -> dict:
    payload = {"model": model, "temperature": 0.2, "max_tokens": 900, "response_format": {"type": "json_object"}, "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]}
    headers = {"Authorization": f"Bearer {settings.openrouter_api_key}"}
    for delay in (0, 1, 3):
        if delay:
            await asyncio.sleep(delay)
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(f"{settings.openrouter_base_url}/v1/chat/completions", headers=headers, json=payload)
                response.raise_for_status()
                return json.loads(response.json()["choices"][0]["message"]["content"])
        except (httpx.HTTPError, KeyError, TypeError, json.JSONDecodeError):
            continue
    raise UnderstandingError("Incident understanding failed")


async def understand(*, incident_text: str, language: Literal["hi", "en"], user_context: object | None) -> UnderstandingResult:
    if language not in {"hi", "en"}:
        raise UnderstandingError("Unsupported incident language")
    prompt = f"Incident (language: {language}): {incident_text}\nUser-supplied context: state={_context_value(user_context, 'state') or 'null'}, roleCategory={_context_value(user_context, 'role_category') or _context_value(user_context, 'roleCategory') or 'null'}"
    corrective = "\nReturn only valid JSON matching the requested schema."
    for model, text in ((settings.openrouter_model_primary, prompt), (settings.openrouter_model_primary, prompt + corrective), (settings.openrouter_model_fallback, prompt)):
        try:
            return UnderstandingResult.model_validate(await _call(model, text))
        except (UnderstandingError, ValueError):
            continue
    raise UnderstandingError("Incident understanding failed")
