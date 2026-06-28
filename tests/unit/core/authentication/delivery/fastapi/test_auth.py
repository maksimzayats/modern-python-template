from typing import Any, cast

import pytest
from fastapi import HTTPException
from starlette.requests import Request
from starlette.types import Scope

from fastapi_template.core.authentication.delivery.fastapi.auth import (
    JWTAuth,
    JWTAuthWithPermissions,
)
from fastapi_template.core.authentication.services.jwt import JWTService
from fastapi_template.core.user.entities import User
from fastapi_template.core.user.use_cases import GetActiveUserByIdUseCase


class FakeJWTService:
    EXPIRED_SIGNATURE_ERROR = JWTService.EXPIRED_SIGNATURE_ERROR
    INVALID_TOKEN_ERROR = JWTService.INVALID_TOKEN_ERROR

    def __init__(
        self,
        *,
        payload: dict[str, Any] | None = None,
        error: Exception | None = None,
    ) -> None:
        self._payload = payload or {}
        self._error = error

    def decode_token(self, *, token: str) -> dict[str, Any]:
        if self._error is not None:
            raise self._error

        return self._payload


class FakeGetActiveUserByIdUseCase:
    def __init__(self, *, user: User | None) -> None:
        self._user = user

    async def execute(self, *, user_id: int) -> User | None:
        return self._user


@pytest.mark.anyio
async def test_jwt_auth_returns_none_when_credentials_are_optional_and_missing() -> None:
    auth = _build_auth(payload={"sub": "1"}, user=_build_user())
    auth.auto_error = False

    assert await auth(_request()) is None


@pytest.mark.anyio
async def test_jwt_auth_rejects_payload_without_subject() -> None:
    auth = _build_auth(payload={}, user=_build_user())

    with pytest.raises(HTTPException) as exc_info:
        await auth(_request(token=_bearer_token()))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token payload missing 'sub' field"


@pytest.mark.anyio
async def test_jwt_auth_rejects_payload_with_invalid_subject() -> None:
    auth = _build_auth(payload={"sub": "not-an-int"}, user=_build_user())

    with pytest.raises(HTTPException) as exc_info:
        await auth(_request(token=_bearer_token()))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token payload has invalid 'sub' field"


@pytest.mark.anyio
async def test_jwt_auth_rejects_missing_active_user() -> None:
    auth = _build_auth(payload={"sub": "1"}, user=None)

    with pytest.raises(HTTPException) as exc_info:
        await auth(_request(token=_bearer_token()))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "User not found"


@pytest.mark.anyio
async def test_jwt_auth_maps_expired_token_error() -> None:
    auth = _build_auth(
        payload={},
        user=_build_user(),
        error=JWTService.EXPIRED_SIGNATURE_ERROR(),
    )

    with pytest.raises(HTTPException) as exc_info:
        await auth(_request(token=_bearer_token()))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token has expired"


@pytest.mark.anyio
async def test_jwt_auth_maps_invalid_token_error() -> None:
    auth = _build_auth(
        payload={},
        user=_build_user(),
        error=JWTService.INVALID_TOKEN_ERROR(),
    )

    with pytest.raises(HTTPException) as exc_info:
        await auth(_request(token=_bearer_token()))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token"


@pytest.mark.anyio
async def test_jwt_auth_rejects_missing_staff_permission() -> None:
    auth = _build_permission_auth(require_staff=True, user=_build_user(is_staff=False))

    with pytest.raises(HTTPException) as exc_info:
        await auth(_request(token=_bearer_token()))

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Staff access required"


@pytest.mark.anyio
async def test_jwt_auth_rejects_missing_superuser_permission() -> None:
    auth = _build_permission_auth(require_superuser=True, user=_build_user(is_superuser=False))

    with pytest.raises(HTTPException) as exc_info:
        await auth(_request(token=_bearer_token()))

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Superuser access required"


def _build_auth(
    *,
    payload: dict[str, Any],
    user: User | None,
    error: Exception | None = None,
) -> JWTAuth:
    return JWTAuth(
        jwt_service=cast(JWTService, FakeJWTService(payload=payload, error=error)),
        get_active_user_by_id_use_case=cast(
            GetActiveUserByIdUseCase,
            FakeGetActiveUserByIdUseCase(user=user),
        ),
    )


def _build_permission_auth(
    *,
    user: User,
    require_staff: bool = False,
    require_superuser: bool = False,
) -> JWTAuthWithPermissions:
    return JWTAuthWithPermissions(
        jwt_service=cast(JWTService, FakeJWTService(payload={"sub": str(user.id)})),
        get_active_user_by_id_use_case=cast(
            GetActiveUserByIdUseCase,
            FakeGetActiveUserByIdUseCase(user=user),
        ),
        require_staff=require_staff,
        require_superuser=require_superuser,
    )


def _request(*, token: str | None = None) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if token is not None:
        headers.append((b"authorization", f"Bearer {token}".encode()))

    scope: Scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/users/me",
        "raw_path": b"/api/v1/users/me",
        "query_string": b"",
        "headers": headers,
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "scheme": "http",
    }
    return Request(scope)


def _build_user(
    *,
    is_staff: bool = True,
    is_superuser: bool = True,
) -> User:
    return User(
        id=1,
        username="test_user",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password_hash=_password_hash(),
        is_staff=is_staff,
        is_superuser=is_superuser,
    )


def _bearer_token() -> str:
    return "signed-jwt-value"


def _password_hash() -> str:
    return "argon2-hash-value"
