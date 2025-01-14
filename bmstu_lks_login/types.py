"""Type definitions for BMSTU LKS Login Library."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class TokenInfo:
    """Information extracted from a portal token."""
    raw_token: str  # The original token string
    decoded_data: dict  # The decoded token data
    expiration: datetime  # Token expiration time
    name: Optional[str] = None  # User's name if available


@dataclass
class LoginResponse:
    """Response from a successful login attempt."""
    login_token: TokenInfo  # The portal3_login token info
    info_token: TokenInfo  # The portal3_info token info
    student_id: Optional[str] = None  # Student ID if available
    group: Optional[str] = None  # Student group if available
