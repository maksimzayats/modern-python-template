from dataclasses import dataclass
from typing import Any, cast

from diwire import Injected
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from throttled import Quota, RateLimiterType, RedisStore, Throttled
from throttled.asyncio import (
    Quota as AsyncQuota,
    RateLimiterType as AsyncRateLimiterType,
    RedisStore as AsyncRedisStore,
    Throttled as AsyncThrottled,
)

from fastapi_template.foundation.factories import BaseFactory


class ThrottledRedisSettings(BaseSettings):
    """Define ThrottledRedisSettings."""

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    url: SecretStr


@dataclass(kw_only=True)
class ThrottlerStoreFactory(BaseFactory):
    """Define ThrottlerStoreFactory."""

    _redis_settings: Injected[ThrottledRedisSettings]

    def __call__(self) -> RedisStore:
        """Build a synchronous Redis throttling store.

        Returns:
        A Redis-backed throttling store.
        """
        return RedisStore(server=self._redis_settings.url.get_secret_value())


@dataclass(kw_only=True)
class ThrottlerFactory(BaseFactory):
    """Define ThrottlerFactory."""

    _store_factory: Injected[ThrottlerStoreFactory]

    def __post_init__(self) -> None:
        """Run post init."""
        self._store = self._store_factory()

    def __call__(
        self,
        quota: Quota,
        using: RateLimiterType = RateLimiterType.TOKEN_BUCKET,
    ) -> Throttled:
        """Build a synchronous throttler.

        Returns:
        A configured throttler.
        """
        return Throttled(
            using=using.value,
            quota=quota,
            store=cast(Any, self._store),
        )


@dataclass(kw_only=True)
class AsyncThrottlerStoreFactory(BaseFactory):
    """Define AsyncThrottlerStoreFactory."""

    _redis_settings: Injected[ThrottledRedisSettings]

    def __call__(self) -> AsyncRedisStore:
        """Build an async Redis throttling store.

        Returns:
        An async Redis-backed throttling store.
        """
        return AsyncRedisStore(server=self._redis_settings.url.get_secret_value())


@dataclass(kw_only=True)
class AsyncThrottlerFactory(BaseFactory):
    """Define AsyncThrottlerFactory."""

    _store_factory: Injected[AsyncThrottlerStoreFactory]

    def __post_init__(self) -> None:
        """Run post init."""
        self._store = self._store_factory()

    def __call__(
        self,
        quota: AsyncQuota,
        using: AsyncRateLimiterType = AsyncRateLimiterType.TOKEN_BUCKET,
    ) -> AsyncThrottled:
        """Build an async throttler.

        Returns:
        A configured async throttler.
        """
        return AsyncThrottled(
            using=using.value,
            quota=quota,
            store=cast(Any, self._store),
        )
