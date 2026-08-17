"""PS-25 Main FastAPI application.

Entrypoint for Uvicorn deployment:
    uvicorn main:app --host 0.0.0.0 --port $PORT
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.router import get_current_user, router as auth_router
from common.config import settings
from common.db import close_db, create_tables, get_async_session
from common.exceptions import (
    AppException,
    ErrorCode,
    app_exception_handler,
    generic_exception_handler,
)
from common.models import User, UserContext
from common.response import APIResponse, error_response, success_response
from evidence.router import router as evidence_router
from incident.router import router as incident_router
from legalaid.router import router as legalaid_router
from triage.retrieval import _embedding, is_ready, load_index
from triage.stt import load_model as load_stt_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize database schema, preload AI/RAG assets, and handle shutdown."""
    # 1. Database schema creation via SQLAlchemy.metadata.create_all() — no Alembic
    create_tables()

    # 2. Whisper model initialization (loaded once at startup)
    try:
        load_stt_model()
    except Exception:
        pass

    # 3. Embedding model initialization (loaded once at startup)
    try:
        _embedding()
    except Exception:
        pass

    # 4. FAISS index + metadata loading (load_index records readiness internally)
    load_index()

    yield

    # Dispose database connection pool on shutdown
    await close_db()


app = FastAPI(
    title="PS-25 Legal Triage API",
    description="Grounded AI Legal Triage Engine (HAQSETU)",
    version="2.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register global exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# ---------------------------------------------------------------------------
# Users Router (PUT /users/context — SSOT 03 §8.5)
# ---------------------------------------------------------------------------


class UserContextRequest(BaseModel):
    """Request payload for updating user context."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    state: Optional[str] = None
    role_category: Optional[str] = Field(default=None, alias="roleCategory")
    vulnerability_tags: Optional[list[str]] = Field(
        default=None, alias="vulnerabilityTags"
    )


class UserContextResponse(BaseModel):
    """Response payload for user context update."""

    saved: bool = True


users_router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@users_router.put(
    "/context",
    response_model=APIResponse[UserContextResponse],
    status_code=status.HTTP_200_OK,
)
async def update_user_context(
    request: UserContextRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> APIResponse[UserContextResponse]:
    """Create or update user context using PATCH-like semantics on a PUT route."""
    stmt = select(UserContext).where(UserContext.user_id == current_user.id)
    result = await db.execute(stmt)
    ctx = result.scalar_one_or_none()

    sent_fields = request.model_dump(exclude_unset=True)

    if ctx is None:
        ctx = UserContext(
            id=uuid.uuid4(),
            user_id=current_user.id,
            state=sent_fields.get("state"),
            role_category=sent_fields.get("role_category"),
            vulnerability_tags=sent_fields.get("vulnerability_tags"),
        )
        db.add(ctx)
    else:
        if "state" in sent_fields:
            ctx.state = sent_fields["state"]
        if "role_category" in sent_fields:
            ctx.role_category = sent_fields["role_category"]
        if "vulnerability_tags" in sent_fields:
            ctx.vulnerability_tags = sent_fields["vulnerability_tags"]
        ctx.updated_at = func.now()

    await db.commit()

    payload = UserContextResponse(saved=True)
    return APIResponse[UserContextResponse].model_validate(
        success_response(payload)
    )


# ---------------------------------------------------------------------------
# Health Endpoint (GET /health — SSOT 03 §13)
# ---------------------------------------------------------------------------


class HealthData(BaseModel):
    """Health status payload."""

    status: str = "ok"


@app.get(
    "/health",
    response_model=APIResponse[HealthData],
    status_code=status.HTTP_200_OK,
    tags=["Health"],
)
async def health_check() -> JSONResponse:
    """Check application health and legal retrieval index readiness."""
    if is_ready():
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=success_response({"status": "ok"}),
        )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_response(
            code=ErrorCode.RETRIEVAL_UNAVAILABLE.value,
            message="Legal retrieval is unavailable.",
        ),
    )


# ---------------------------------------------------------------------------
# Register Public Routers
# ---------------------------------------------------------------------------

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(incident_router)
app.include_router(evidence_router)
app.include_router(legalaid_router)


__all__ = [
    "app",
]
