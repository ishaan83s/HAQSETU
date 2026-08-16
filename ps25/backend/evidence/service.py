"""Evidence lookup service.

Provides deterministic, database-backed evidence checklists for supported
incident types.

The LLM never generates evidence data. All evidence comes from the seeded
EvidenceChecklist table defined by the frozen PS-25 SSOT.
"""

from __future__ import annotations

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.models import EvidenceChecklist


FALLBACK_INCIDENT_TYPE = "unsupported"


async def get_for_issues(
    db: AsyncSession,
    issue_types: List[str],
) -> List[str]:
    """Return the deduplicated evidence checklist for multiple issue types.

    Each issue type is resolved against the seeded EvidenceChecklist table.
    If an issue type has no direct row, the seeded ``unsupported`` row is used.

    Items preserve their original seed order within each checklist, and the
    union uses first-seen-wins ordering across all requested issue types.

    Args:
        db: Active async SQLAlchemy session.
        issue_types: Issue type strings from the triage result.

    Returns:
        Flat, deduplicated, first-seen-wins ordered list of evidence items.
    """

    if not issue_types:
        issue_types = [FALLBACK_INCIDENT_TYPE]

    requested_types = list(dict.fromkeys(issue_types))

    result = await db.execute(
        select(EvidenceChecklist).where(
            EvidenceChecklist.incident_type.in_(requested_types)
        )
    )

    rows = result.scalars().all()
    rows_by_type = {
        row.incident_type: row
        for row in rows
    }

    fallback_result = await db.execute(
        select(EvidenceChecklist).where(
            EvidenceChecklist.incident_type == FALLBACK_INCIDENT_TYPE
        )
    )
    fallback_row = fallback_result.scalar_one()

    evidence_items: List[str] = []
    seen: set[str] = set()

    for issue_type in requested_types:
        row = rows_by_type.get(issue_type, fallback_row)

        for item in row.items:
            if item not in seen:
                seen.add(item)
                evidence_items.append(item)

    return evidence_items


async def get_for_incident_type(
    db: AsyncSession,
    incident_type: str,
) -> dict[str, object]:
    """Return the public evidence payload for one incident type.

    Unknown incident types resolve to the seeded ``unsupported`` checklist
    while preserving the originally requested incident type in the response
    contract only when it is known. Unknown types therefore return the
    fallback row's incident type.
    """

    result = await db.execute(
        select(EvidenceChecklist).where(
            EvidenceChecklist.incident_type == incident_type
        )
    )

    row = result.scalar_one_or_none()

    if row is None:
        fallback_result = await db.execute(
            select(EvidenceChecklist).where(
                EvidenceChecklist.incident_type == FALLBACK_INCIDENT_TYPE
            )
        )
        row = fallback_result.scalar_one()

    return {
        "incidentType": row.incident_type,
        "items": list(row.items),
    }


__all__ = [
    "FALLBACK_INCIDENT_TYPE",
    "get_for_issues",
    "get_for_incident_type",
]