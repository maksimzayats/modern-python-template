from abc import ABC, abstractmethod

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class HealthRepository(ABC):
    """Define HealthRepository."""

    @abstractmethod
    async def check_database(self) -> None:
        """Check database readiness."""
        raise NotImplementedError


class SQLAlchemyHealthRepository(HealthRepository):
    """Define SQLAlchemyHealthRepository."""

    def __init__(self, *, session: AsyncSession) -> None:
        """Initialize the instance."""
        self._session = session

    async def check_database(self) -> None:
        """Run check database."""
        await self._session.execute(text("SELECT 1"))
