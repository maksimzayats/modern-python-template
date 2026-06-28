from fastapi_template.core.exceptions import ApplicationError


class UserError(ApplicationError):
    """Define UserError."""


class WeakPasswordError(UserError):
    """Define WeakPasswordError."""


class UserAlreadyExistsError(UserError):
    """Define UserAlreadyExistsError."""
