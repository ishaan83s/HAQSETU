"""The single OpenRouter extraction-and-classification call."""
from __future__ import annotations

import asyncio
import json
from typing import Literal

import httpx

from common.config import settings
from triage.exceptions import UnderstandingError
from triage.schemas import UnderstandingResult

SYSTEM_PROMPT = """You extract structured facts and classify the legal issue in a citizen's incident
description. You do not give legal advice or interpretation — you only identify
what the person is describing.

Supported issue types (choose 1 or 2, never more):
- wage_nonpayment: salary/wages unpaid or withheld
- wrongful_termination: fired/dismissed, including retaliatory termination
- tenancy_eviction: eviction, illegal lockout, tenancy disputes
- unsupported: use this alone if nothing above clearly applies

Rules:
1. Assign a confidence 0.0-1.0 to every issue you output. Only include an issue if
   its confidence is >= 0.5. If nothing reaches 0.5, output exactly one issue:
   {"type": "unsupported", "confidence": 1.0}.
2. tenancy_eviction never appears together with wage_nonpayment or wrongful_termination
   in the same output — these are different domains. If your reasoning suggests both,
   keep only the single highest-confidence issue.
3. jurisdictionState is "Maharashtra" only if the text or the provided user-supplied
   state clearly indicates Maharashtra. Otherwise it is null. Never guess a different
   state — no other state value is ever valid for this field.
4. urgency precedence, apply in this exact order and stop at the first match:
   a. "urgent" if the text describes eviction/lockout language, OR any safety/threat
      language directed at the person.
   b. "time_sensitive" if the text describes a statutory notice period, a deadline,
      or termination combined with a wage issue.
   c. otherwise "general".
5. actor is a short role description of who the incident is about/against
   (e.g. "employer", "landlord"), or null if genuinely unclear from the text.
6. what is a short one-sentence summary of the core issue, always present, never empty.
7. where/when are short free-text fragments taken from what the person actually said —
   do not infer a specific date or place that wasn't stated.
8. If user-supplied context is absent (state and roleCategory both null/missing),
   treat both as unknown. Do NOT infer a state or role from the incident text alone
   to fill this gap beyond what rule 3 already allows for jurisdictionState — the
   user-supplied context fields are a separate, optional input signal, not something
   to backfill from your own reasoning.
9. Output ONLY the JSON object matching the schema below. No prose, no markdown fences.

Output schema:
{
  "actor": "string or null",
  "what": "string",
  "where": "string or null",
  "when": "string or null",
  "issues": [ { "type": "string", "confidence": 0.0 } ],
  "jurisdictionState": "Maharashtra or null",
  "urgency": "general | time_sensitive | urgent"
}"""


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
