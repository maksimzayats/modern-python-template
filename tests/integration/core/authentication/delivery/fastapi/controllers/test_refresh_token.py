from http import HTTPStatus

import anyio
import pytest
from diwire import Container
from sqlalchemy import update

from fastapi_template.core.authentication.delivery.fastapi.schemas.token_response import (
    TokenResponseSchema,
)
from fastapi_template.core.user.entities.user import User
from fastapi_template.core.user.infrastructure.sqlalchemy.models.user import UserModel
from fastapi_template.infrastructure.sqlalchemy.session import SQLAlchemySessionFactory
from tests.integration.factories import TestClientFactory, TestUserFactory

_TEST_PASSWORD = "test-password"  # noqa: S105


@pytest.fixture(scope="function")
def user(user_factory: TestUserFactory) -> User:
    return user_factory(username="test", password=_TEST_PASSWORD)


def test_refresh_token_rotates_refresh_session(
    test_client_factory: TestClientFactory,
    user: User,
) -> None:
    with test_client_factory() as test_client:
        response = test_client.post(
            "/api/v1/auth/token",
            json={"username": user.username, "password": _TEST_PASSWORD},
        )
        token_response = TokenResponseSchema.model_validate(response.json())

        response = test_client.post(
            "/api/v1/auth/token/refresh",
            json={"refresh_token": token_response.refresh_token},
        )
        token_data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert set(token_data) == {"access_token", "refresh_token"}
    assert token_data["refresh_token"] != token_response.refresh_token


def test_refresh_token_rejects_inactive_session_user(
    container: Container,
    test_client_factory: TestClientFactory,
    user: User,
) -> None:
    with test_client_factory() as test_client:
        response = test_client.post(
            "/api/v1/auth/token",
            json={"username": user.username, "password": _TEST_PASSWORD},
        )
        token_response = TokenResponseSchema.model_validate(response.json())

        anyio.run(_deactivate_user, container, user.id)

        response = test_client.post(
            "/api/v1/auth/token/refresh",
            json={"refresh_token": token_response.refresh_token},
        )

    assert response.status_code == HTTPStatus.UNAUTHORIZED


async def _deactivate_user(container: Container, user_id: int) -> None:
    session_factory = container.resolve(SQLAlchemySessionFactory)
    async with session_factory() as session:
        await session.execute(
            update(UserModel).where(UserModel.id == user_id).values(is_active=False),
        )
        await session.commit()
