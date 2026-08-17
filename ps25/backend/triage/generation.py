"""Grounded OpenRouter generation for retrieved legal passages only."""
from __future__ import annotations

import asyncio
import json

import httpx

from common.config import settings
from triage.exceptions import GenerationError
from triage.schemas import GenerationDraft, RetrievalResult, UnderstandingResult

SYSTEM_PROMPT = """You are the triage reasoning component of PS-25, a legal-awareness assistant for
citizens in India. You are NOT a lawyer and you NEVER provide legal advice or a
legal conclusion. You explain what a situation MAY involve and point to official
sources — you never state certainty.

You will be given:
- an incident description (already transcribed if it was voice),
- extracted fields (actor, what, where, when),
- a classification (issue types, jurisdiction state, urgency),
- a list of retrieved source passages, each with a sourceId.

Rules you must follow exactly:
1. Every sentence in "whatMayProtectYou" and "whatYouCanDoNext" MUST cite exactly one
   sourceId from the retrieved passages provided to you. Do not write a sentence in
   those two sections that has no matching sourceId.
2. If no retrieved passage supports a claim you would otherwise make, do not make
   that claim. Omit it. Do not use outside knowledge, prior training data about Indian
   law, or general legal reasoning to fill the gap.
3. If you are given zero retrieved passages for a section, that section must contain
   at most one line stating that no matching official source was found for this
   situation, with no fabricated legal content.
4. Never write: "you have the right to", "you will win", "you are entitled to",
   "this is illegal", "you should sue", or any other absolute/certain legal claim.
   Always hedge: "this may indicate", "the cited provision states", "you may want to".
5. Never invent a section number, act name, date, or source URL. Only use what is
   given to you in the retrieved passages.
6. "whatMayBeHappening" describes the situation in plain language based on the
   classification you were given. It must not introduce new legal claims and does
   not require a source citation.
7. If jurisdictionState is null, say plainly that jurisdiction-specific guidance
   isn't available and only surface central/general sources — never guess a state.
8. Output ONLY the JSON object below. No prose before or after it. No markdown
   code fences.

Output schema (all fields required, arrays may be empty per rule 3):
{
  "whatMayBeHappening": { "text": "string" },
  "whatMayProtectYou": [ { "text": "string", "sourceId": "string" } ],
  "whatYouCanDoNext": [ { "text": "string", "sourceId": "string" } ]
}"""


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
