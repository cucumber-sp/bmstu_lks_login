"""BMSTU LKS Login Library

This library provides functionality to authenticate with the BMSTU LKS portal
and obtain JWT tokens for further API access.
"""

from .client import BmstuLksClient, LoginError
from .types import LoginResponse, TokenInfo

__version__ = "0.1.0"
__all__ = ["BmstuLksClient", "LoginError", "LoginResponse", "TokenInfo"]
