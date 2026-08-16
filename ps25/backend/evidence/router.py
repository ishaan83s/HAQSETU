"""Evidence API router.

Exposes the deterministic, database-backed evidence checklist endpoint.
Authentication is enforced through the shared Auth dependency.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from auth.router import get_current_user
from common.db import get_async_session
from common.models import User
from common.response import APIResponse, success_response
from evidence.service import get_for_incident_type


class EvidenceResponse(BaseModel):
    """Public response payload for a single evidence checklist lookup."""

    model_config = ConfigDict(populate_by_name=True)

    incident_type: str = Field(alias="incidentType")
    items: list[str]


router = APIRouter(
    prefix="/evidence",
    tags=["Evidence"],
)


@router.get(
    "/{incident_type}",
    response_model=APIResponse[EvidenceResponse],
    status_code=200,
)
async def get_evidence(
    incident_type: str,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> APIResponse[EvidenceResponse]:
    """Return the evidence checklist for an incident type."""

    payload = await get_for_incident_type(
        db=db,
        incident_type=incident_type,
    )

    evidence = EvidenceResponse.model_validate(payload)

    return APIResponse[EvidenceResponse].model_validate(
        success_response(evidence)
    )


__all__ = [
    "EvidenceResponse",
    "router",
]