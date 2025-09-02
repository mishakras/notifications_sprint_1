from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str


class TokenExpiredResponse(ErrorResponse):
    detail: str = "Token has expired"


class InvalidTokenSignatureResponse(ErrorResponse):
    detail: str = "Invalid token signature"


class DuplicateEmailResponse(ErrorResponse):
    detail: str = "Email already registered"


class InvalidCredentialsResponse(ErrorResponse):
    detail: str = "Invalid credentials"


class RefreshTokenExpiredResponse(ErrorResponse):
    detail: str = "Refresh token expired or revoked"


class UserNotFoundResponse(ErrorResponse):
    detail: str = "User not found"


class OldPasswordIncorrectResponse(ErrorResponse):
    detail: str = "Old password is incorrect"


class NoLoginHistoryResponse(ErrorResponse):
    detail: str = "No login history found"


class ChangeCredentialsErrorResponse(ErrorResponse):
    detail: str

    class Config:
        schema_extra = {
            "examples": [
                {"detail": "Email already registered"},
                {"detail": "Old password is incorrect"},
            ],
        }
