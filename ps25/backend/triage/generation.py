"""Grounded OpenRouter generation for retrieved legal passages only."""
from __future__ import annotations

import asyncio
import json

import httpx

from common.config import settings
from triage.exceptions import GenerationError
from triage.schemas import GenerationDraft, RetrievalResult, UnderstandingResult

SYSTEM_PROMPT = """You are PS-25's legal-awareness triage component, not a lawyer. Output only JSON with whatMayBeHappening:{text}, whatMayProtectYou:[{text,sourceId}], whatYouCanDoNext:[{text,sourceId}]. Every claim in the latter arrays must cite exactly one provided sourceId. Do not use outside knowledge, invent sources, or make certain legal claims such as 'you have the right to', 'you will win', 'you are entitled to', 'this is illegal', or 'you should sue'."""


async def _request(model: str, prompt: str) -> dict:
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
    raise GenerationError("Grounded generation failed")


def _guardrail(understanding: UnderstandingResult, message: str) -> GenerationDraft:
    return GenerationDraft.model_validate({"whatMayBeHappening": {"text": understanding.what}, "whatMayProtectYou": [], "whatYouCanDoNext": [{"text": message, "sourceId": ""}]})


async def generate(*, incident_text: str, language: str, understanding: UnderstandingResult, retrieval: RetrievalResult) -> GenerationDraft:
    if [issue.type for issue in understanding.issues] == ["unsupported"]:
        return _guardrail(understanding, "No matching official source was found for this situation.")
    if not retrieval.results:
        return _guardrail(understanding, "No matching official source was found for this situation.")
    sources = "\n".join(f'- sourceId: {row.source_id}, title: "{row.source.title}", section: "{row.source.section}", text: "{row.passage}"' for row in retrieval.results)
    prompt = f"Incident (language: {language}): {incident_text}\nExtracted: actor={understanding.actor}, what={understanding.what}, where={understanding.where}, when={understanding.when}\nClassification: issues={[issue.model_dump() for issue in understanding.issues]}, jurisdictionState={understanding.jurisdiction_state}, urgency={understanding.urgency}\nRetrieved sources:\n{sources}"
    offered = {row.source_id for row in retrieval.results}
    corrective = "\nYour previous output was invalid JSON or used an unknown sourceId. Return only valid JSON using only listed sourceIds."
    for model, text in ((settings.openrouter_model_primary, prompt), (settings.openrouter_model_primary, prompt + corrective), (settings.openrouter_model_fallback, prompt)):
        try:
            draft = GenerationDraft.model_validate(await _request(model, text))
            for claims in (draft.what_may_protect_you, draft.what_you_can_do_next):
                if any(claim.source_id not in offered for claim in claims):
                    raise ValueError("Unknown source id")
            return draft
        except (GenerationError, ValueError):
            continue
    raise GenerationError("Grounded generation failed")
