from typing import Any, cast

import pytest
from pydantic import SecretStr
from throttled import Quota
from throttled.asyncio import Quota as AsyncQuota

from fastapi_template.infrastructure.throttled import throttler as throttler_module
from fastapi_template.infrastructure.throttled.throttler import (
    AsyncThrottlerFactory,
    AsyncThrottlerStoreFactory,
    ThrottledRedisSettings,
    ThrottlerFactory,
    ThrottlerStoreFactory,
)


class FakeStore:
    def __init__(self, *, server: str) -> None:
        self.server = server


class FakeThrottled:
    def __init__(self, *, using: str, quota: object, store: object) -> None:
        self.using = using
        self.quota = quota
        self.store = store


class FakeStoreFactory:
    def __init__(self, *, store: FakeStore) -> None:
        self.store = store

    def __call__(self) -> FakeStore:
        return self.store


def test_sync_throttler_factories_build_store_and_throttler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(throttler_module, "RedisStore", FakeStore)
    monkeypatch.setattr(throttler_module, "Throttled", FakeThrottled)

    store = ThrottlerStoreFactory(_redis_settings=_redis_settings())()
    result = ThrottlerFactory(
        _store_factory=cast(ThrottlerStoreFactory, FakeStoreFactory(store=cast(FakeStore, store))),
    )(cast(Quota, object()))
    fake_result = cast(Any, result)

    assert cast(FakeStore, store).server == "redis://localhost:6379/0"
    assert fake_result.store is store
    assert fake_result.using == "token_bucket"


def test_async_throttler_factories_build_store_and_throttler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(throttler_module, "AsyncRedisStore", FakeStore)
    monkeypatch.setattr(throttler_module, "AsyncThrottled", FakeThrottled)

    store = AsyncThrottlerStoreFactory(_redis_settings=_redis_settings())()
    result = AsyncThrottlerFactory(
        _store_factory=cast(
            AsyncThrottlerStoreFactory,
            FakeStoreFactory(store=cast(FakeStore, store)),
        ),
    )(cast(AsyncQuota, object()))
    fake_result = cast(Any, result)

    assert cast(FakeStore, store).server == "redis://localhost:6379/0"
    assert fake_result.store is store
    assert fake_result.using == "token_bucket"


def _redis_settings() -> ThrottledRedisSettings:
    return ThrottledRedisSettings(url=SecretStr("redis://localhost:6379/0"))
