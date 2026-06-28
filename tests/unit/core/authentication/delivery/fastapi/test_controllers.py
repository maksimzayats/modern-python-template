from typing import cast

import pytest
from fastapi import HTTPException

from fastapi_template.core.authentication.delivery.fastapi.auth import JWTAuthFactory
from fastapi_template.core.authentication.delivery.fastapi.controllers import (
    AuthenticationTokenController,
)
from fastapi_template.core.authentication.delivery.fastapi.throttling import UserThrottlerFactory
from fastapi_template.core.authentication.exceptions import (
    InvalidCredentialsError,
    RefreshTokenError,
)
from fastapi_template.core.authentication.use_cases import (
    IssueTokenUseCase,
    RefreshTokenUseCase,
    RevokeTokenUseCase,
)
from fastapi_template.core.shared.delivery.fastapi.request import RequestInfoService
from fastapi_template.core.shared.delivery.fastapi.throttling import IPThrottlerFactory


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("exception", "detail"),
    [
        (InvalidCredentialsError(), "Invalid username or password"),
        (RefreshTokenUseCase.INVALID_REFRESH_TOKEN_ERROR(), "Invalid refresh token"),
        (RevokeTokenUseCase.EXPIRED_REFRESH_TOKEN_ERROR(), "Refresh token expired or revoked"),
        (RefreshTokenError(), "Refresh token error"),
    ],
)
async def test_authentication_controller_translates_domain_errors(
    exception: Exception,
    detail: str,
) -> None:
    controller = _build_controller()

    with pytest.raises(HTTPException) as exc_info:
        await controller.handle_exception(exception)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == detail


@pytest.mark.anyio
async def test_authentication_controller_reraises_unhandled_errors() -> None:
    controller = _build_controller()
    error = RuntimeError("unexpected")

    with pytest.raises(RuntimeError) as exc_info:
        await controller.handle_exception(error)

    assert exc_info.value is error


def _build_controller() -> AuthenticationTokenController:
    return AuthenticationTokenController(
        _jwt_auth_factory=cast(JWTAuthFactory, lambda **_kwargs: object()),
        _request_info_service=cast(RequestInfoService, object()),
        _ip_throttler_factory=cast(IPThrottlerFactory, object()),
        _user_throttler_factory=cast(UserThrottlerFactory, object()),
        _issue_token_use_case=cast(IssueTokenUseCase, object()),
        _refresh_token_use_case=cast(RefreshTokenUseCase, object()),
        _revoke_token_use_case=cast(RevokeTokenUseCase, object()),
    )
