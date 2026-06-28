from enum import StrEnum

from pydantic_settings import BaseSettings


class Environment(StrEnum):
    """Define Environment."""

    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"
    CI = "ci"


class ApplicationSettings(BaseSettings):
    """Define ApplicationSettings."""

    environment: Environment = Environment.PRODUCTION
    version: str = "0.1.0"
    time_zone: str = "UTC"
