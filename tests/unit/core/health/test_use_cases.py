import pytest

from fastdjango.core.health import use_cases as health_use_cases
from fastdjango.core.health.use_cases import SystemHealthUseCase


class BrokenSessionManager:
    async def afirst(self) -> None:
        msg = "database unavailable"
        raise RuntimeError(msg)


class BrokenSession:
    objects = BrokenSessionManager()


@pytest.mark.anyio
async def test_health_check_maps_unexpected_errors_to_health_check_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(health_use_cases, "Session", BrokenSession)

    with pytest.raises(SystemHealthUseCase.HEALTH_CHECK_ERROR):
        await SystemHealthUseCase().check()
