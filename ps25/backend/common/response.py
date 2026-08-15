"""API response envelope as mandated by the Architectural Overrides.

Every endpoint MUST return exactly:
    {
      "success": true,
      "data": {},
      "error": null
    }

This module provides:
  - APIResponse: a generic Pydantic model enforcing the envelope structure
  - success_response(): helper to build a success envelope
  - error_response(): helper to build an error envelope
"""
from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, field_validator


class ErrorInfo(BaseModel):
    """Error detail embedded in the API envelope on failure.

    Fields:
      - code: frozen error code from the registry (SSOT 03 §14.2)
      - message: human-readable message
    """

    code: str
    message: str


class APIResponse(BaseModel, Generic[T]):
    """Canonical API response envelope.

    SSOT 03 §14.1 / Architectural Override #2:
    Every endpoint MUST return exactly:
        {"success": true, "data": {}, "error": null}  on success, or
        {"success": false, "data": null, "error": {...}} on failure.
    """

    success: bool
    data: Optional[T] = None
    error: Optional[ErrorInfo] = None

    @field_validator("success")
    @classmethod
    def validate_envelope(cls, v: bool) -> bool:
        """Ensure the envelope is internally consistent."""
        return v


def success_response(data: Any = None, success: bool = True) -> dict:
    """Build a success envelope dictionary.

    Args:
        data: The payload to return (defaults to empty dict).
        success: Always True for success responses.

    Returns:
        dict: {"success": True, "data": data, "error": None}
    """
    if data is None:
        data = {}
    return {"success": True, "data": data, "error": None}


def error_response(
    code: str,
    message: str,
    data: Any = None,
) -> dict:
    """Build an error envelope dictionary.

    Args:
        code: Frozen error code from the registry.
        message: Human-readable error message.
        data: Optional additional data (defaults to None).

    Returns:
        dict: {"success": False, "data": null or data, "error": {"code": code, "message": message}}
    """
    if data is None:
        data = None
    return {
        "success": False,
        "data": data,
        "error": {"code": code, "message": message},
    }


__all__ = [
    "APIResponse",
    "ErrorInfo",
    "success_response",
    "error_response",
]