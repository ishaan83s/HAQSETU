"""Global exception handling and frozen error-code registry.

SSOT 03 §14.2: The complete error registry must be frozen before implementation.
Below is the frozen registry with exact code, HTTP status, and message mappings.

Error codes (frozen):
  INVALID_PHONE           — 422
  INVALID_OTP             — 401
  UNAUTHORIZED            — 401
  FORBIDDEN               — 403
  INVALID_INPUT           — 422
  EMPTY_INCIDENT          — 422
  INCIDENT_NOT_FOUND      — 404
  TRIAGE_UNAVAILABLE      — 502
  STT_FAILED              — 502
  RETRIEVAL_UNAVAILABLE   — 502
  GENERATION_FAILED       — 502
  NO_RELEVANT_SOURCE      — 502
  UNSUPPORTED_DOMAIN      — 422
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, Optional, Tuple

from fastapi import Request, status
from fastapi.responses import JSONResponse

from common.response import error_response


class ErrorCode(str, Enum):
    """Frozen error code registry (SSOT 03 §14.2).

    Each member maps to an HTTP status code and a human-readable message.
    No module may invent its own error codes beyond these.
    """

    INVALID_PHONE = "INVALID_PHONE"
    INVALID_OTP = "INVALID_OTP"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_INPUT = "INVALID_INPUT"
    EMPTY_INCIDENT = "EMPTY_INCIDENT"
    INCIDENT_NOT_FOUND = "INCIDENT_NOT_FOUND"
    TRIAGE_UNAVAILABLE = "TRIAGE_UNAVAILABLE"
    STT_FAILED = "STT_FAILED"
    RETRIEVAL_UNAVAILABLE = "RETRIEVAL_UNAVAILABLE"
    GENERATION_FAILED = "GENERATION_FAILED"
    NO_RELEVANT_SOURCE = "NO_RELEVANT_SOURCE"
    UNSUPPORTED_DOMAIN = "UNSUPPORTED_DOMAIN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_MALFORMED = "TOKEN_MALFORMED"


# ── HTTP status + default message mapping ──────────────────────────────
_ERROR_STATUS_MAP: Dict[ErrorCode, Tuple[int, str]] = {
    ErrorCode.INVALID_PHONE: (status.HTTP_422_UNPROCESSABLE_ENTITY, "Phone number must be a valid 10-digit Indian number."),
    ErrorCode.INVALID_OTP: (status.HTTP_401_UNAUTHORIZED, "Invalid OTP. Please try again."),
    ErrorCode.UNAUTHORIZED: (status.HTTP_401_UNAUTHORIZED, "Authentication required."),
    ErrorCode.FORBIDDEN: (status.HTTP_403_FORBIDDEN, "Access denied."),
    ErrorCode.INVALID_INPUT: (status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid request payload."),
    ErrorCode.EMPTY_INCIDENT: (status.HTTP_422_UNPROCESSABLE_ENTITY, "Incident text cannot be empty."),
    ErrorCode.INCIDENT_NOT_FOUND: (status.HTTP_404_NOT_FOUND, "Incident not found."),
    ErrorCode.TRIAGE_UNAVAILABLE: (status.HTTP_502_BAD_GATEWAY, "Triage service temporarily unavailable. Please retry."),
    ErrorCode.STT_FAILED: (status.HTTP_502_BAD_GATEWAY, "Speech-to-text failed. Please try typing instead."),
    ErrorCode.RETRIEVAL_UNAVAILABLE: (status.HTTP_502_BAD_GATEWAY, "Legal source retrieval failed."),
    ErrorCode.GENERATION_FAILED: (status.HTTP_502_BAD_GATEWAY, "Response generation failed."),
    ErrorCode.NO_RELEVANT_SOURCE: (status.HTTP_502_BAD_GATEWAY, "No relevant legal sources found."),
    ErrorCode.UNSUPPORTED_DOMAIN: (status.HTTP_422_UNPROCESSABLE_ENTITY, "This legal domain is not yet supported."),
    ErrorCode.TOKEN_EXPIRED: (status.HTTP_401_UNAUTHORIZED, "Token has expired."),
    ErrorCode.TOKEN_MALFORMED: (status.HTTP_401_UNAUTHORIZED, "Token is malformed."),
}




class AppException(Exception):
    """Base application exception with frozen error code.

    All module-level exceptions inherit from this class, ensuring a
    consistent error envelope through the global exception handler.
    """

    def __init__(
        self,
        code: ErrorCode,
        message: Optional[str] = None,
        status_code: Optional[int] = None,
        data: Optional[dict] = None,
    ):
        self.code = code
        if message is None:
            _, message = get_error_status(code)
        self.message = message
        if status_code is None:
            status_code, _ = get_error_status(code)
        self.status_code = status_code
        self.data = data
        super().__init__(self.message)


# ── Module-specific convenience exceptions ─────────────────────────────

class AuthException(AppException):
    """Authentication-related exceptions."""

    def __init__(self, code: ErrorCode = ErrorCode.UNAUTHORIZED, message: Optional[str] = None, data: Optional[dict] = None):
        super().__init__(code, message=message, data=data)


class ValidationException(AppException):
    """Input validation exceptions."""

    def __init__(self, message: Optional[str] = None, data: Optional[dict] = None):
        super().__init__(ErrorCode.INVALID_INPUT, message=message, data=data)


class TriagedException(AppException):
    """Triaze / AI pipeline exceptions."""

    def __init__(self, code: ErrorCode = ErrorCode.TRIAGE_UNAVAILABLE, message: Optional[str] = None, data: Optional[dict] = None):
        super().__init__(code, message=message, data=data)


# ── Global exception handler ───────────────────────────────────────────
def create_exception_handler():
    """Create a global exception handler for AppException.

    This handler catches AppException instances and returns a consistent
    error envelope: {"success": false, "data": null, "error": {"code": ..., "message": ...}}
    """
    async def _handler(request: Request, exc: AppException) -> JSONResponse:
        body = error_response(
            code=exc.code.value,
            message=exc.message,
            data=exc.data,
        )
        return JSONResponse(status_code=exc.status_code, content=body)

    return _handler


# ── FastAPI exception handler registration ────────────────────────────
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Global handler registered on the FastAPI app."""
    body = error_response(
        code=exc.code.value,
        message=exc.message,
        data=exc.data,
    )
    return JSONResponse(status_code=exc.status_code, content=body)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unhandled exceptions.

    Prevents stack traces from leaking to the client (SSOT 09 §34.5).
    """
    body = error_response(
        code="INTERNAL_ERROR",
        message="An internal server error occurred. Please try again later.",
    )
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=body)


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