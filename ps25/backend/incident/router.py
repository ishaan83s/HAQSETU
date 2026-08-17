"""Incident API router.

Implements the frozen endpoints:
- POST /incidents (status 201 on incident creation, status 200 on empty transcription)
- GET /incidents/{id} (status 200 on success, status 404 if not found / foreign user)
"""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from auth.router import get_current_user
from common.db import get_async_session
from common.models import User
from common.response import APIResponse, success_response
from incident.schemas import (
    EmptyTranscriptionResponse,
    IncidentRequest,
    IncidentResponse,
)
from incident.service import create_incident, get_incident_by_id

router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"],
)


@router.post(
    "",
    response_model=APIResponse[Any],
    status_code=status.HTTP_201_CREATED,
)
async def post_incident(
    request: IncidentRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> JSONResponse:
    """Create and triage a new incident from voice or text."""
    result = await create_incident(
        db=db,
        current_user=current_user,
        request=request,
    )

    if isinstance(result, EmptyTranscriptionResponse):
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=success_response(result.model_dump(by_alias=True, mode="json")),
        )

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=success_response(result.model_dump(by_alias=True, mode="json")),
    )


@router.get(
    "/{id}",
    response_model=APIResponse[IncidentResponse],
    status_code=status.HTTP_200_OK,
)
async def get_incident(
    id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> APIResponse[IncidentResponse]:
    """Retrieve an existing incident by ID for the authenticated owner."""
    result = await get_incident_by_id(
        db=db,
        current_user=current_user,
        incident_id=id,
    )

    return APIResponse[IncidentResponse].model_validate(
        success_response(result.model_dump(by_alias=True, mode="json"))
    )


__all__ = ["router"]
