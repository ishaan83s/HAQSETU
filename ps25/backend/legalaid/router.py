"""Legal-aid API router.

Exposes the deterministic, database-backed legal-aid contact lookup.
Authentication is enforced through the shared Auth dependency.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from auth.router import get_current_user
from common.db import get_async_session
from common.models import User
from common.response import APIResponse, success_response
from legalaid.service import get_for_state


class LegalAidContactResponse(BaseModel):
    """Public legal-aid contact representation."""

    model_config = ConfigDict(populate_by_name=True)

    name: str
    contact_info: str = Field(alias="contactInfo")


class LegalAidResponse(BaseModel):
    """Public legal-aid response payload."""

    contacts: list[LegalAidContactResponse]


router = APIRouter(
    prefix="/legal-aid",
    tags=["Legal Aid"],
)


@router.get(
    "",
    response_model=APIResponse[LegalAidResponse],
    status_code=200,
)
async def get_legal_aid(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    state: str | None = Query(default=None),
) -> APIResponse[LegalAidResponse]:
    """Return the full ordered legal-aid contact list for a state."""

    contacts = await get_for_state(
        db=db,
        state=state,
    )

    payload = LegalAidResponse(
        contacts=[
            LegalAidContactResponse.model_validate(contact, from_attributes=True)
            for contact in contacts
        ]
    )

    return APIResponse[LegalAidResponse].model_validate(
        success_response(payload)
    )


__all__ = [
    "LegalAidContactResponse",
    "LegalAidResponse",
    "router",
]