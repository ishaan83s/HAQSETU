"""Authentication API router.

Implements the frozen public authentication endpoints:

- POST /auth/request-otp
- POST /auth/verify-otp

Business logic remains in auth.service.
This module is responsible only for HTTP routing, dependency wiring,
response-envelope composition, and response-model validation.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from auth.schemas import OtpRequest, OtpResponse, OtpVerifyRequest, TokenResponse
from auth.service import (
    create_access_token,
    get_or_create_user,
    normalize_phone_number,
    verify_otp,
)
from common.db import get_async_session
from common.response import APIResponse, success_response


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/request-otp",
    response_model=APIResponse[OtpResponse],
    status_code=200,
)
async def request_otp(
    request: OtpRequest,
) -> APIResponse[OtpResponse]:
    """Validate the phone number and acknowledge the mock OTP request.

    The MVP does not send a real SMS. The service only normalizes and
    validates the supplied phone number; the actual OTP value remains
    internal to the mock authentication flow.
    """

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


__all__ = ["router"]