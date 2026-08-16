"""Canonical API response envelope.

Every API endpoint MUST return exactly one of the two frozen envelope shapes:

Success:
    {
        "success": true,
        "data": <payload>,
        "error": null
    }

Error:
    {
        "success": false,
        "data": null,
        "error": {
            "code": "STRING",
            "message": "string"
        }
    }

The envelope contract is defined by PS25 Modular SSOTs v2.0.
"""

from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, model_validator


T = TypeVar("T")


class ErrorInfo(BaseModel):
    """Error detail embedded in the API envelope on failure."""

    code: str
    message: str


class APIResponse(BaseModel, Generic[T]):
    """Canonical API response envelope.

    Success responses require:
        success=True
        data=<payload>
        error=None

    Error responses require:
        success=False
        data=None
        error=<ErrorInfo>
    """

    success: bool
    data: Optional[T] = None
    error: Optional[ErrorInfo] = None

    @model_validator(mode="after")
    def validate_envelope(self) -> "APIResponse[T]":
        """Enforce the frozen success/error envelope invariants."""

        if self.success:
            if self.data is None:
                raise ValueError(
                    "Successful responses require non-null data."
                )

            if self.error is not None:
                raise ValueError(
                    "Successful responses require error to be null."
                )

        else:
            if self.data is not None:
                raise ValueError(
                    "Error responses require data to be null."
                )

            if self.error is None:
                raise ValueError(
                    "Error responses require a non-null error."
                )

        return self


def success_response(data: Any = None) -> dict:
    """Build a canonical success response envelope.

    If no payload is supplied, the data field is represented by an
    empty object rather than null.
    """

    if data is None:
        data = {}

    return {
        "success": True,
        "data": data,
        "error": None,
    }


def error_response(code: str, message: str) -> dict:
    """Build a canonical error response envelope.

    Error responses always contain null data.
    """

    return {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
        },
    }


__all__ = [
    "APIResponse",
    "ErrorInfo",
    "success_response",
    "error_response",
]