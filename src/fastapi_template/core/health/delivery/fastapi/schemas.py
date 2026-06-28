from typing import Literal

from fastapi_template.foundation.delivery.fastapi.schemas import BaseFastAPISchema


class HealthCheckResponseSchema(BaseFastAPISchema):
    """Define HealthCheckResponseSchema."""

    status: Literal["ok"]
