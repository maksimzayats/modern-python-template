from fastapi_template.core.authentication.dtos import IssueTokenDTO, RefreshTokenDTO, TokenDTO
from fastapi_template.foundation.delivery.fastapi.schemas import BaseFastAPISchema


class IssueTokenRequestSchema(IssueTokenDTO, BaseFastAPISchema):
    """Define IssueTokenRequestSchema."""


class RefreshTokenRequestSchema(RefreshTokenDTO, BaseFastAPISchema):
    """Define RefreshTokenRequestSchema."""


class TokenResponseSchema(TokenDTO, BaseFastAPISchema):
    """Define TokenResponseSchema."""
