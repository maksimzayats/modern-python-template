import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fastapi_template.core.authentication.dtos import CreateRefreshSessionDTO
from fastapi_template.core.authentication.entities import RefreshSession
from fastapi_template.core.authentication.models import (
    RefreshSessionModel,
    ensure_aware_datetime,
    optional_aware_datetime,
)
from fastapi_template.core.user.entities import User
from fastapi_template.core.user.repositories import user_from_model


class RefreshSessionRepository(ABC):
    """Define RefreshSessionRepository."""

    @abstractmethod
    async def create(self, *, data: CreateRefreshSessionDTO) -> RefreshSession:
        """Create a refresh session.

        Returns:
            The created refresh session.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_token_hash(self, *, refresh_token_hash: str) -> RefreshSession | None:
        """Get a refresh session by token hash.

        Returns:
            The matching refresh session, if one exists.
        """
        raise NotImplementedError

    @abstractmethod
    async def replace_token_hash(
        self,
        *,
        session_id: uuid.UUID,
        refresh_token_hash: str,
        last_used_at: datetime,
        rotation_counter: int,
    ) -> RefreshSession | None:
        """Replace the refresh token hash for a session.

        Returns:
            The updated refresh session, if one exists.
        """
        raise NotImplementedError

    @abstractmethod
    async def revoke(self, *, session_id: uuid.UUID, revoked_at: datetime) -> None:
        """Revoke a refresh session."""
        raise NotImplementedError


class SQLAlchemyRefreshSessionRepository(RefreshSessionRepository):
    """Define SQLAlchemyRefreshSessionRepository."""

    def __init__(self, *, session: AsyncSession) -> None:
        """Initialize the instance."""
        self._session = session

    async def create(self, *, data: CreateRefreshSessionDTO) -> RefreshSession:
        """Run create.

        Returns:
        The operation result.
        """
        model = RefreshSessionModel(
            refresh_token_hash=data.refresh_token_hash,
            user_id=data.user.id,
            user_agent=data.user_agent,
            ip_address_trace=data.ip_address_trace,
            expires_at=data.expires_at,
        )

        self._session.add(model)
        await self._session.flush()

        return refresh_session_from_model(model=model, user=data.user)

    async def get_by_token_hash(self, *, refresh_token_hash: str) -> RefreshSession | None:
        """Run get by token hash.

        Returns:
        The operation result.
        """
        query_result = await self._session.execute(
            select(RefreshSessionModel)
            .options(selectinload(RefreshSessionModel.user))
            .where(RefreshSessionModel.refresh_token_hash == refresh_token_hash),
        )
        model = query_result.scalar_one_or_none()

        if model is None:
            return None

        return refresh_session_from_model(model=model)

    async def replace_token_hash(
        self,
        *,
        session_id: uuid.UUID,
        refresh_token_hash: str,
        last_used_at: datetime,
        rotation_counter: int,
    ) -> RefreshSession | None:
        """Run replace token hash.

        Returns:
        The operation result.
        """
        query_result = await self._session.execute(
            select(RefreshSessionModel)
            .options(selectinload(RefreshSessionModel.user))
            .where(RefreshSessionModel.id == session_id)
            .with_for_update(),
        )
        model = query_result.scalar_one_or_none()
        if model is None:
            return None

        model.refresh_token_hash = refresh_token_hash
        model.rotation_counter = rotation_counter
        model.last_used_at = last_used_at

        return refresh_session_from_model(model=model)

    async def revoke(self, *, session_id: uuid.UUID, revoked_at: datetime) -> None:
        """Run revoke."""
        query_result = await self._session.execute(
            select(RefreshSessionModel)
            .where(RefreshSessionModel.id == session_id)
            .with_for_update(),
        )
        model = query_result.scalar_one_or_none()
        if model is None:
            return

        model.revoked_at = revoked_at


def refresh_session_from_model(
    *,
    model: RefreshSessionModel,
    user: User | None = None,
) -> RefreshSession:
    """Run refresh session from model.

    Returns:
    The operation result.
    """
    return RefreshSession(
        id=model.id,
        refresh_token_hash=model.refresh_token_hash,
        user=user or user_from_model(model=model.user),
        user_agent=model.user_agent,
        ip_address_trace=model.ip_address_trace,
        created_at=ensure_aware_datetime(model.created_at),
        last_used_at=optional_aware_datetime(model.last_used_at),
        expires_at=ensure_aware_datetime(model.expires_at),
        revoked_at=optional_aware_datetime(model.revoked_at),
        rotation_counter=model.rotation_counter,
    )
