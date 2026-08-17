"""Deterministic P2 guardrails and source resolution."""
from __future__ import annotations

import re

from triage.exceptions import GenerationError
from triage.schemas import ClaimWithSource, GenerationDraft, RetrievalResult, TriageCards, TriageResult, UnderstandingResult

FORBIDDEN = re.compile(r"\b(you have the right to|you will win|you are entitled to|this is illegal|you should sue)\b", re.IGNORECASE)


def normalize_issues(issues):
    best = {}
    for issue in issues:
        if issue.confidence >= 0.5 and (issue.type not in best or issue.confidence > best[issue.type].confidence):
            best[issue.type] = issue
    ordered = sorted(best.values(), key=lambda issue: issue.confidence, reverse=True)
    supported = [issue for issue in ordered if issue.type != "unsupported"]
    if supported:
        ordered = supported
    if any(issue.type == "tenancy_eviction" for issue in ordered) and any(issue.type in {"wage_nonpayment", "wrongful_termination"} for issue in ordered):
        ordered = [ordered[0]]
    if ordered:
        return ordered[:2]
    unsupported = next((issue for issue in issues if issue.type == "unsupported"), None)
    return [unsupported] if unsupported is not None else []


def validate(*, understanding: UnderstandingResult, draft: GenerationDraft, retrieval: RetrievalResult) -> TriageResult:
    issues = normalize_issues(understanding.issues)
    if not issues:
        raise GenerationError("No valid issue labels")
    sources = {row.source_id: row.source for row in retrieval.results}

    def resolve(claims):
        resolved = []
        for claim in claims:
            if claim.source_id not in sources:
                continue
            if FORBIDDEN.search(claim.text):
                raise GenerationError("Generated claim used forbidden certainty language")
            resolved.append(ClaimWithSource(text=claim.text, source=sources[claim.source_id]))
        return resolved

    return TriageResult(
        issues=issues,
        actor=understanding.actor,
        jurisdictionState=understanding.jurisdiction_state,
        urgency=understanding.urgency,
        cards=TriageCards(
            whatMayBeHappening=draft.what_may_be_happening,
            whatMayProtectYou=resolve(draft.what_may_protect_you),
            whatYouCanDoNext=resolve(draft.what_you_can_do_next),
        ),
    )
