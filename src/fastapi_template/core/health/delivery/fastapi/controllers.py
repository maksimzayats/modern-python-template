from dataclasses import dataclass
from http import HTTPStatus

from diwire import Injected
from fastapi import APIRouter, HTTPException, WebSocket
from starlette import status

from fastapi_template.core.health.delivery.fastapi.schemas import HealthCheckResponseSchema
from fastapi_template.core.health.use_cases import SystemHealthUseCase
from fastapi_template.foundation.delivery.controllers import BaseAsyncController


@dataclass(kw_only=True)
class HealthController(BaseAsyncController):
    """Define HealthController."""

    _system_health_use_case: Injected[SystemHealthUseCase]

    def register(self, registry: APIRouter) -> None:
        """Run register."""
        registry.add_api_route(
            path="/api/v1/health",
            endpoint=self.health_check,
            methods=["GET"],
            response_model=HealthCheckResponseSchema,
        )
        registry.add_api_websocket_route(
            path="/api/v1/health/ws",
            endpoint=self.health_check_websocket,
        )

    async def health_check(self) -> HealthCheckResponseSchema:
        """Run health check.

        Returns:
        The operation result.
        """
        try:
            await self._system_health_use_case.execute()
        except SystemHealthUseCase.HEALTH_CHECK_ERROR as exception:
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="Service is unavailable",
            ) from exception

        return HealthCheckResponseSchema(status="ok")

    async def health_check_websocket(self, websocket: WebSocket) -> None:
        """Run health check websocket."""
        await websocket.accept()

        try:
            await self._system_health_use_case.execute()
        except SystemHealthUseCase.HEALTH_CHECK_ERROR:
            await websocket.send_json({"status": "unavailable"})
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            return

        await websocket.send_json(HealthCheckResponseSchema(status="ok").model_dump())
        await websocket.close()
