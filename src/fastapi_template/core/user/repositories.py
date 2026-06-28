from abc import ABC, abstractmethod
from typing import ClassVar

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_template.core.user.dtos import CreateUserDTO
from fastapi_template.core.user.entities import User
from fastapi_template.core.user.exceptions import UserAlreadyExistsError
from fastapi_template.core.user.models import UserModel


class UserRepository(ABC):
    """Define UserRepository."""

    @abstractmethod
    async def get_by_id(self, *, user_id: int) -> User | None:
        """Get a user by identifier.

        Returns:
            The matching user, if one exists.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_active_by_id(self, *, user_id: int) -> User | None:
        """Get an active user by identifier.

        Returns:
            The matching active user, if one exists.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_username(self, *, username: str) -> User | None:
        """Get a user by username.

        Returns:
            The matching user, if one exists.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_username_or_email(self, *, username: str, email: str) -> User | None:
        """Get a user by username or email.

        Returns:
            The matching user, if one exists.
        """
        raise NotImplementedError

    @abstractmethod
    async def create(self, *, data: CreateUserDTO, password_hash: str) -> User:
        """Create a user.

        Returns:
            The created user.
        """
        raise NotImplementedError

    @abstractmethod
    async def set_access_flags(
        self,
        *,
        user_id: int,
        is_staff: bool,
        is_superuser: bool,
    ) -> User | None:
        """Set staff and superuser flags.

        Returns:
            The updated user, if one exists.
        """
        raise NotImplementedError


class SQLAlchemyUserRepository(UserRepository):
    """Define SQLAlchemyUserRepository."""

    USER_ALREADY_EXISTS_ERROR: ClassVar = UserAlreadyExistsError
    INTEGRITY_ERROR: ClassVar = IntegrityError

    def __init__(self, *, session: AsyncSession) -> None:
        """Initialize the instance."""
        self._session = session

    async def get_by_id(self, *, user_id: int) -> User | None:
        """Run get by id.

        Returns:
        The operation result.
        """
        model = await self._session.get(UserModel, user_id)

        if model is None:
            return None

        return user_from_model(model=model)

    async def get_active_by_id(self, *, user_id: int) -> User | None:
        """Run get active by id.

        Returns:
        The operation result.
        """
        query_result = await self._session.execute(
            select(UserModel).where(
                UserModel.id == user_id,
                UserModel.is_active.is_(True),
            ),
        )
        model = query_result.scalar_one_or_none()

        if model is None:
            return None

        return user_from_model(model=model)

    async def get_by_username(self, *, username: str) -> User | None:
        """Run get by username.

        Returns:
        The operation result.
        """
        query_result = await self._session.execute(
            select(UserModel).where(UserModel.username == username),
        )
        model = query_result.scalar_one_or_none()

        if model is None:
            return None

        return user_from_model(model=model)

    async def get_by_username_or_email(self, *, username: str, email: str) -> User | None:
        """Run get by username or email.

        Returns:
        The operation result.
        """
        query_result = await self._session.execute(
            select(UserModel).where(
                or_(
                    UserModel.username == username,
                    UserModel.email == email,
                ),
            ),
        )
        model = query_result.scalar_one_or_none()

        if model is None:
            return None

        return user_from_model(model=model)

    async def create(self, *, data: CreateUserDTO, password_hash: str) -> User:
        """Run create.

        Returns:
        The operation result.
        """
        model = UserModel(
            username=data.username,
            email=str(data.email),
            first_name=data.first_name,
            last_name=data.last_name,
            password_hash=password_hash,
        )

        try:
            await _create_model(session=self._session, model=model)
        except self.INTEGRITY_ERROR as exception:
            raise self.USER_ALREADY_EXISTS_ERROR from exception

        return user_from_model(model=model)

    async def set_access_flags(
        self,
        *,
        user_id: int,
        is_staff: bool,
        is_superuser: bool,
    ) -> User | None:
        """Run set access flags.

        Returns:
        The operation result.
        """
        model = await self._session.get(UserModel, user_id)
        if model is None:
            return None

        model.is_staff = is_staff
        model.is_superuser = is_superuser
        await self._session.flush()

        return user_from_model(model=model)


def user_from_model(*, model: UserModel) -> User:
    """Run user from model.

    Returns:
    The operation result.
    """
    return User(
        id=model.id,
        username=model.username,
        email=model.email,
        first_name=model.first_name,
        last_name=model.last_name,
        password_hash=model.password_hash,
        is_active=model.is_active,
        is_staff=model.is_staff,
        is_superuser=model.is_superuser,
    )


async def _create_model(*, session: AsyncSession, model: UserModel) -> None:
    session.add(model)
    await session.flush()
