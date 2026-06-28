from datetime import datetime

from fastapi_template.core.user.entities import User
from fastapi_template.foundation.dtos import BaseDTO


class IssueTokenDTO(BaseDTO):
    """Define IssueTokenDTO."""

    username: str
    password: str


class TokenRequestContextDTO(BaseDTO):
    """Define TokenRequestContextDTO."""

    user_agent: str
    ip_address_trace: str | None


class RefreshTokenDTO(BaseDTO):
    """Define RefreshTokenDTO."""

    refresh_token: str


class CreateRefreshSessionDTO(BaseDTO):
    """Define CreateRefreshSessionDTO."""

    user: User
    refresh_token_hash: str
    user_agent: str
    ip_address_trace: str
    expires_at: datetime


class TokenDTO(BaseDTO):
    """Define TokenDTO."""

    access_token: str
    refresh_token: str
