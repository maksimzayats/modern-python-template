from dataclasses import dataclass

from diwire import Injected
from fastapi import APIRouter, FastAPI
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from fastapi_template.core.authentication.delivery.fastapi.controllers import (
    AuthenticationTokenController,
)
from fastapi_template.core.health.delivery.fastapi.controllers import HealthController
from fastapi_template.core.user.delivery.fastapi.controllers import UserController
from fastapi_template.foundation.factories import BaseFactory
from fastapi_template.infrastructure.logfire.instrumentor import OpenTelemetryInstrumentor
from fastapi_template.infrastructure.shared import ApplicationSettings, Environment


class FastAPISettings(BaseSettings):
    """Define FastAPISettings."""

    allowed_hosts: list[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1"])


class CORSSettings(BaseSettings):
    """Define CORSSettings."""

    model_config = SettingsConfigDict(env_prefix="CORS_")

    allow_credentials: bool = True
    allow_origins: list[str] = Field(default_factory=lambda: ["http://localhost"])
    allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    allow_headers: list[str] = Field(default_factory=lambda: ["*"])


@dataclass(kw_only=True)
class FastAPIFactory(BaseFactory):
    """Define FastAPIFactory."""

    _application_settings: Injected[ApplicationSettings]
    _fastapi_settings: Injected[FastAPISettings]
    _cors_settings: Injected[CORSSettings]

    _telemetry_instrumentor: Injected[OpenTelemetryInstrumentor]

    _health_controller: Injected[HealthController]
    _authentication_token_controller: Injected[AuthenticationTokenController]
    _user_controller: Injected[UserController]

    def __call__(
        self,
        *,
        add_trusted_hosts_middleware: bool = True,
        add_cors_middleware: bool = True,
    ) -> FastAPI:
        """Run call.

        Returns:
        The operation result.
        """
        docs_url: str | None = None
        if self._application_settings.environment is not Environment.PRODUCTION:
            docs_url = "/docs"

        app = FastAPI(
            title="API",
            docs_url=docs_url,
            redoc_url=None,
        )

        self._telemetry_instrumentor.instrument_fastapi(app=app)
        self._add_middlewares(
            app=app,
            add_trusted_hosts_middleware=add_trusted_hosts_middleware,
            add_cors_middleware=add_cors_middleware,
        )
        self._register_controllers(app=app)

        return app

    def _add_middlewares(
        self,
        app: FastAPI,
        *,
        add_trusted_hosts_middleware: bool = True,
        add_cors_middleware: bool = True,
    ) -> None:
        if add_trusted_hosts_middleware:
            app.add_middleware(
                TrustedHostMiddleware,
                allowed_hosts=self._fastapi_settings.allowed_hosts,
            )

        if add_cors_middleware:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=self._cors_settings.allow_origins,
                allow_credentials=self._cors_settings.allow_credentials,
                allow_methods=self._cors_settings.allow_methods,
                allow_headers=self._cors_settings.allow_headers,
            )

    def _register_controllers(
        self,
        app: FastAPI,
    ) -> None:
        health_router = APIRouter(tags=["health"])
        self._health_controller.register(health_router)
        app.include_router(health_router)

        auth_router = APIRouter(tags=["auth", "token"])
        self._authentication_token_controller.register(auth_router)
        app.include_router(auth_router)

        user_router = APIRouter(tags=["user"])
        self._user_controller.register(user_router)
        app.include_router(user_router)
