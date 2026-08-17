"""Global exception handling and frozen error-code registry.

The error registry and exception behavior are defined by the PS25
Modular SSOTs v2.0.

Application errors use the canonical API response envelope:

{
    "success": false,
    "data": null,
    "error": {
        "code": "STRING",
        "message": "string"
    }
}
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, Optional, Tuple

from fastapi import Request, status
from fastapi.responses import JSONResponse

from common.response import error_response


class ErrorCode(str, Enum):
    """Frozen API error-code registry."""

    INVALID_PHONE = "INVALID_PHONE"
    INVALID_OTP = "INVALID_OTP"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_INPUT = "INVALID_INPUT"
    EMPTY_INCIDENT = "EMPTY_INCIDENT"
    INCIDENT_NOT_FOUND = "INCIDENT_NOT_FOUND"

    STT_FAILED = "STT_FAILED"
    UNDERSTANDING_FAILED = "UNDERSTANDING_FAILED"
    RETRIEVAL_UNAVAILABLE = "RETRIEVAL_UNAVAILABLE"
    GENERATION_FAILED = "GENERATION_FAILED"
    TRIAGE_UNAVAILABLE = "TRIAGE_UNAVAILABLE"


# Frozen HTTP status + default message mapping.
_ERROR_STATUS_MAP: Dict[ErrorCode, Tuple[int, str]] = {
    ErrorCode.INVALID_PHONE: (
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "Phone number must be a valid 10-digit Indian number.",
    ),
    ErrorCode.INVALID_OTP: (
        status.HTTP_401_UNAUTHORIZED,
        "Invalid OTP. Please try again.",
    ),
    ErrorCode.UNAUTHORIZED: (
        status.HTTP_401_UNAUTHORIZED,
        "Authentication required.",
    ),
    ErrorCode.FORBIDDEN: (
        status.HTTP_403_FORBIDDEN,
        "Access denied.",
    ),
    ErrorCode.INVALID_INPUT: (
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "Invalid request payload.",
    ),
    ErrorCode.EMPTY_INCIDENT: (
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "Incident text cannot be empty.",
    ),
    ErrorCode.INCIDENT_NOT_FOUND: (
        status.HTTP_404_NOT_FOUND,
        "Incident not found.",
    ),
    ErrorCode.STT_FAILED: (
        status.HTTP_502_BAD_GATEWAY,
        "Speech-to-text failed. Please try typing instead.",
    ),
    ErrorCode.UNDERSTANDING_FAILED: (
        status.HTTP_502_BAD_GATEWAY,
        "Incident understanding failed. Please retry.",
    ),
    ErrorCode.RETRIEVAL_UNAVAILABLE: (
        status.HTTP_502_BAD_GATEWAY,
        "Legal source retrieval failed. Please retry.",
    ),
    ErrorCode.GENERATION_FAILED: (
        status.HTTP_502_BAD_GATEWAY,
        "Response generation failed. Please retry.",
    ),
    ErrorCode.TRIAGE_UNAVAILABLE: (
        status.HTTP_502_BAD_GATEWAY,
        "Triage service temporarily unavailable. Please retry.",
    ),
}


def get_error_status(code: ErrorCode) -> Tuple[int, str]:
    """Return the frozen HTTP status and default message for an error code."""

    try:
        return _ERROR_STATUS_MAP[code]
    except KeyError as exc:
        raise ValueError(
            f"Unknown error code: {code}"
        ) from exc


class AppException(Exception):
    """Base application exception using the frozen error registry."""

    def __init__(
        self,
        code: ErrorCode,
        message: Optional[str] = None,
    ) -> None:
        self.code = code

        status_code, default_message = get_error_status(code)

        self.status_code = status_code
        self.message = message or default_message

        super().__init__(self.message)


class AuthException(AppException):
    """Authentication-related application exception."""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.UNAUTHORIZED,
        message: Optional[str] = None,
    ) -> None:
        super().__init__(
            code=code,
            message=message,
        )


class ValidationException(AppException):
    """Input validation application exception."""

    def __init__(
        self,
        message: Optional[str] = None,
    ) -> None:
        super().__init__(
            code=ErrorCode.INVALID_INPUT,
            message=message,
        )


class TriagedException(AppException):
    """AI/ML triage pipeline application exception."""

    def __init__(
        self,
        code: ErrorCode = ErrorCode.TRIAGE_UNAVAILABLE,
        message: Optional[str] = None,
    ) -> None:
        super().__init__(
            code=code,
            message=message,
        )


def create_exception_handler():
    """Create a FastAPI handler for AppException instances."""

    async def _handler(
        request: Request,
        exc: AppException,
    ) -> JSONResponse:
        body = error_response(
            code=exc.code.value,
            message=exc.message,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=body,
        )

    return _handler


async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    """Global FastAPI handler for known application exceptions."""

    body = error_response(
        code=exc.code.value,
        message=exc.message,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=body,
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Catch-all handler for unexpected exceptions.

    Raw exception details and stack traces are never exposed to clients.
    Unexpected failures are represented by the frozen TRIAGE_UNAVAILABLE
    contract rather than an invented INTERNAL_ERROR code.
    """

    status_code, message = get_error_status(
        ErrorCode.TRIAGE_UNAVAILABLE
    )

    body = error_response(
        code=ErrorCode.TRIAGE_UNAVAILABLE.value,
        message=message,
    )

    return JSONResponse(
        status_code=status_code,
        content=body,
    )


__all__ = [
    "ErrorCode",
    "AppException",
    "AuthException",
    "ValidationException",
    "TriagedException",
    "get_error_status",
    "create_exception_handler",
    "app_exception_handler",
    "generic_exception_handler",
]