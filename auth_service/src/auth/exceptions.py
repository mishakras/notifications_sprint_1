from fastapi import HTTPException, status


class CustomHTTPException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class TokenExpiredException(CustomHTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )


class InvalidTokenSignatureException(CustomHTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token signature",
        )


class DuplicateUsernameException(CustomHTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )


class InsufficientPermissionsException(CustomHTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )


class AlreadyRegisteredUserException(CustomHTTPException):
    def __init__(self, user_email):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User {user_email} already registered",
        )


class InvalidCredentialsException(CustomHTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credentials",
        )


class UserNotFoundException(CustomHTTPException):
    def __init__(self, status_code=status.HTTP_401_UNAUTHORIZED):
        super().__init__(
            status_code=status_code,
            detail="User not found",
        )


class NoLoginHistoryFoundException(CustomHTTPException):
    def __init__(self, user_email):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No login history found",
        )


class OldPasswordIsIncorrectException(CustomHTTPException):
    def __init__(self, user_email):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect",
        )


class AlreadyRegisteredRoleException(CustomHTTPException):
    def __init__(self, role_name):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role {role_name} already registered",
        )


class RoleNotFoundException(CustomHTTPException):
    def __init__(self, role_name):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
