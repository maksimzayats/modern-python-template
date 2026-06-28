from fastapi_template.core.user.dtos import CreateUserDTO, UserDTO
from fastapi_template.foundation.delivery.fastapi.schemas import BaseFastAPISchema


class CreateUserRequestSchema(CreateUserDTO, BaseFastAPISchema):
    """Define CreateUserRequestSchema."""


class UserSchema(UserDTO, BaseFastAPISchema):
    """Define UserSchema."""
