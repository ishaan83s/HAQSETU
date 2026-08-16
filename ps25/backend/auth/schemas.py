"""Auth request/response schemas.

Defines the Pydantic models for authentication endpoints:
- POST /auth/request-otp
- POST /auth/verify-otp
"""

from __future__ import annotations

from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class OtpRequest(BaseModel):
    """Request schema for OTP request endpoint."""
    phone_number: str = Field(..., alias="phoneNumber")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "phoneNumber": "+919876543210"
            }
        }
    )


class OtpVerifyRequest(BaseModel):
    """Request schema for OTP verification endpoint."""
    phone_number: str = Field(..., alias="phoneNumber")
    otp: str = Field(..., min_length=6, max_length=6)

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "phoneNumber": "+919876543210",
                "otp": "123456"
            }
        }
    )


class OtpResponse(BaseModel):
    """Response schema for OTP request endpoint."""
    otp_sent: bool = Field(..., alias="otpSent")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "otpSent": True
            }
        }
    )


class TokenResponse(BaseModel):
    """Response schema for OTP verification endpoint."""
    token: str
    user_id: UUID = Field(..., alias="userId")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "userId": "123e4567-e89b-12d3-a456-426614174000"
            }
        }
    )


__all__ = [
    "OtpRequest",
    "OtpVerifyRequest",
    "OtpResponse",
    "TokenResponse",
]
