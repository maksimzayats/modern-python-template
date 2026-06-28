from fastapi_template.core.exceptions import ApplicationError


class AuthenticationError(ApplicationError):
    """Define AuthenticationError."""


class InvalidCredentialsError(AuthenticationError):
    """Define InvalidCredentialsError."""


class RefreshTokenError(AuthenticationError):
    """Define RefreshTokenError."""


class InvalidRefreshTokenError(RefreshTokenError):
    """Define InvalidRefreshTokenError."""


class ExpiredRefreshTokenError(RefreshTokenError):
    """Define ExpiredRefreshTokenError."""
