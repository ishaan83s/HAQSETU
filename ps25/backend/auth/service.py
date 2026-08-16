"""Authentication service layer.

Implements:
- Phone normalization and validation
- Mock OTP verification
- User lookup/creation
- JWT creation and validation support
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.config import settings
from common.exceptions import AuthException, ErrorCode
from common.models import User


def normalize_phone_number(phone: str) -> str:
    """Normalize and validate Indian phone number (SSOT 03 §8.3).
    
    Required behavior:
    1. Strip spaces.
    2. Strip dashes.
    3. If bare 10-digit Indian number, prepend +91.
    4. Validate against ^\\+91[6-9]\\d{9}$
    """
    # 1 & 2. Strip spaces and dashes
    normalized = phone.replace(" ", "").replace("-", "")
    
    # 3. If bare 10-digit Indian number, prepend +91
    if len(normalized) == 10 and normalized.isdigit():
        normalized = f"+91{normalized}"
        
    # 4. Validate the final value against the India-only regex
    if not re.match(r"^\+91[6-9]\d{9}$", normalized):
        raise AuthException(
            code=ErrorCode.INVALID_PHONE,
            message="Invalid phone number format. Must be a valid 10-digit Indian number starting with +91."
        )
        
    return normalized


def verify_otp(submitted_otp: str) -> None:
    """Verify submitted OTP against configured MOCK_OTP (SSOT 03 §8.4).
    
    Submitted OTP must exactly match configured MOCK_OTP.
    Invalid OTP must produce HTTP 401, error code = INVALID_OTP.
    """
    if submitted_otp != settings.mock_otp:
        raise AuthException(code=ErrorCode.INVALID_OTP)


async def get_or_create_user(db: AsyncSession, phone_number: str) -> User:
    """Lookup user by phone or create if unknown (SSOT 03 §8.4).
    
    Auth owns User creation. Uses application-side UUID generation.
    """
    # phone_number is expected to be already normalized
    stmt = select(User).where(User.phone_number == phone_number)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        # Create user with application-side UUID
        user = User(
            id=uuid.uuid4(),
            phone_number=phone_number
        )
        db.add(user)
        # Auth owns persistence of newly created user
        await db.commit()
        await db.refresh(user)
        
    return user


def create_access_token(user_id: uuid.UUID) -> str:
    """Create HS256 JWT for a user (SSOT 03 §8.4).
    
    Claims MUST contain exactly:
    - sub: user UUID as string
    - iat: issued-at timestamp
    - exp: expiry timestamp (exactly 7 days)
    """
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=settings.jwt_access_token_expire_days)
    
    claims = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp())
    }
    
    token = jwt.encode(
        claims,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return token


def validate_token(token: str) -> uuid.UUID:
    """Validate JWT and return user ID (SSOT 03 §8.4).
    
    - uses HS256
    - uses JWT_SECRET
    - validates exp
    - obtains sub
    - rejects malformed/expired/missing-sub
    - failures map to UNAUTHORIZED
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise AuthException(code=ErrorCode.UNAUTHORIZED)
            
        try:
            return uuid.UUID(user_id_str)
        except (ValueError, AttributeError):
            raise AuthException(code=ErrorCode.UNAUTHORIZED)
            
    except JWTError:
        # Rejects malformed or expired JWT
        raise AuthException(code=ErrorCode.UNAUTHORIZED)


__all__ = [
    "normalize_phone_number",
    "verify_otp",
    "get_or_create_user",
    "create_access_token",
    "validate_token",
]

