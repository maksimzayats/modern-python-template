from typing import Any, cast

from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from fastapi_template.core.authentication.delivery.fastapi.controllers import (
    AuthenticationTokenController,
)
from fastapi_template.core.health.delivery.fastapi.controllers import HealthController
from fastapi_template.core.user.delivery.fastapi.controllers import UserController
from fastapi_template.entrypoints.fastapi.factories import (
    CORSSettings,
    FastAPIFactory,
    FastAPISettings,
)
from fastapi_template.infrastructure.logfire.instrumentor import OpenTelemetryInstrumentor
from fastapi_template.infrastructure.shared import ApplicationSettings, Environment


class FakeTelemetryInstrumentor:
    instrumented_app: FastAPI | None = None

    def instrument_fastapi(self, *, app: FastAPI) -> None:
        self.instrumented_app = app


class FakeController:
    registered = False

    def register(self, registry: APIRouter) -> None:
        self.registered = True
        registry.add_api_route("/registered", self.endpoint, methods=["GET"])

    async def endpoint(self) -> dict[str, bool]:
        return {"ok": True}


def test_fastapi_factory_disables_docs_and_optional_middlewares_in_production() -> None:
    instrumentor = FakeTelemetryInstrumentor()
    controllers = [FakeController(), FakeController(), FakeController()]
    app = _build_factory(
        application_settings=ApplicationSettings(environment=Environment.PRODUCTION),
        instrumentor=instrumentor,
        controllers=controllers,
    )(
        add_trusted_hosts_middleware=False,
        add_cors_middleware=False,
    )

    assert app.docs_url is None
    assert app.user_middleware == []
    assert instrumentor.instrumented_app is app
    assert all(controller.registered for controller in controllers)


def test_fastapi_factory_adds_docs_and_default_middlewares_outside_production() -> None:
    app = _build_factory(
        application_settings=ApplicationSettings(environment=Environment.DEVELOPMENT),
        instrumentor=FakeTelemetryInstrumentor(),
    )()

    middleware_names = {cast(Any, middleware.cls).__name__ for middleware in app.user_middleware}
    assert app.docs_url == "/docs"
    assert TrustedHostMiddleware.__name__ in middleware_names
    assert CORSMiddleware.__name__ in middleware_names


def _build_factory(
    *,
    application_settings: ApplicationSettings,
    instrumentor: FakeTelemetryInstrumentor,
    controllers: list[FakeController] | None = None,
) -> FastAPIFactory:
    health_controller, auth_controller, user_controller = controllers or [
        FakeController(),
        FakeController(),
        FakeController(),
    ]
    return FastAPIFactory(
        _application_settings=application_settings,
        _fastapi_settings=FastAPISettings(),
        _cors_settings=CORSSettings(),
        _telemetry_instrumentor=cast(OpenTelemetryInstrumentor, instrumentor),
        _health_controller=cast(HealthController, health_controller),
        _authentication_token_controller=cast(AuthenticationTokenController, auth_controller),
        _user_controller=cast(UserController, user_controller),
    )
