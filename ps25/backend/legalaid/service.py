"""Legal-aid lookup service.

Provides deterministic, database-backed legal-aid contacts.

Legal-aid data is seeded and source-backed. This service does not make
external network calls and does not involve the LLM.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.models import LegalAidContact


FALLBACK_STATE = "central"


async def get_for_state(
    db: AsyncSession,
    state: Optional[str],
) -> list[LegalAidContact]:
    """Return the full ordered legal-aid contact list for a state.

    Unsupported or omitted states resolve to the seeded ``central`` rows.

    Args:
        db: Active async SQLAlchemy session.
        state: Requested jurisdiction state, or None.

    Returns:
        All matching contacts ordered by display_order.
    """

    resolved_state = (
        state
        if state == "Maharashtra"
        else FALLBACK_STATE
    )

    result = await db.execute(
        select(LegalAidContact)
        .where(LegalAidContact.state == resolved_state)
        .order_by(LegalAidContact.display_order)
    )

    return list(result.scalars().all())


async def get_primary_for_state(
    db: AsyncSession,
    state: Optional[str],
) -> LegalAidContact:
    """Return the primary legal-aid contact for a state.

    The primary contact is the row with the lowest display_order.
    Unsupported or omitted states resolve to the seeded ``central`` rows.
    """

    resolved_state = (
        state
        if state == "Maharashtra"
        else FALLBACK_STATE
    )

    result = await db.execute(
        select(LegalAidContact)
        .where(LegalAidContact.state == resolved_state)
        .order_by(LegalAidContact.display_order)
        .limit(1)
    )

    contact = result.scalar_one_or_none()

    if contact is None:
        raise RuntimeError(
            "Legal-aid seed data is missing the required fallback contact."
        )

    return contact


__all__ = [
    "FALLBACK_STATE",
    "get_for_state",
    "get_primary_for_state",
]