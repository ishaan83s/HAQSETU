"""Authentication API router.

Implements the frozen public authentication endpoints:

- POST /auth/request-otp
- POST /auth/verify-otp

Also provides the reusable JWT authentication dependency:

- get_current_user

Business logic remains in auth.service.
This module is responsible only for HTTP routing, dependency wiring,
authentication dependency handling, response-envelope composition,
and response-model validation.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.schemas import OtpRequest, OtpResponse, OtpVerifyRequest, TokenResponse
from auth.service import (
    create_access_token,
    get_or_create_user,
    normalize_phone_number,
    validate_token,
    verify_otp,
)
from common.db import get_async_session
from common.exceptions import AuthException, ErrorCode
from common.models import User
from common.response import APIResponse, success_response


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/request-otp",
    response_model=APIResponse[OtpResponse],
    status_code=200,
)
async def request_otp(
    request: OtpRequest,
) -> APIResponse[OtpResponse]:
    """Validate the phone number and acknowledge the mock OTP request."""

    normalize_phone_number(request.phone_number)

    payload = OtpResponse(otp_sent=True)

    return APIResponse[OtpResponse].model_validate(
        success_response(payload)
    )


@router.post(
    "/verify-otp",
    response_model=APIResponse[TokenResponse],
    status_code=200,
)
async def verify_otp_endpoint(
    request: OtpVerifyRequest,
    db: AsyncSession = Depends(get_async_session),
) -> APIResponse[TokenResponse]:
    """Verify the mock OTP, create/find the user, and issue a JWT."""

    normalized_phone = normalize_phone_number(request.phone_number)

    verify_otp(request.otp)

    user = await get_or_create_user(
        db=db,
        phone_number=normalized_phone,
    )

    token = create_access_token(user.id)

    payload = TokenResponse(
        token=token,
        user_id=user.id,
    )

    return APIResponse[TokenResponse].model_validate(
        success_response(payload)
    )


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_async_session),
) -> User:
    """Resolve the authenticated user from a Bearer JWT.

    Required malformed-header cases all map to UNAUTHORIZED.
    JWT validation itself is delegated to auth.service.validate_token().
    """

    if authorization is None:
        raise AuthException(code=ErrorCode.UNAUTHORIZED)

    parts = authorization.split(" ")

    if len(parts) != 2:
        raise AuthException(code=ErrorCode.UNAUTHORIZED)

    scheme, token = parts

    if scheme != "Bearer" or not token:
        raise AuthException(code=ErrorCode.UNAUTHORIZED)

    user_id: UUID = validate_token(token)

    result = await db.execute(
        select(User).where(User.id == user_id)
    )

    user = result.scalar_one_or_none()

    if user is None:
        raise AuthException(code=ErrorCode.UNAUTHORIZED)

    return user


__all__ = [
    "router",
    "get_current_user",
]