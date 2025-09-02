from auth_service.src.auth import errors as err

# Users

register_schema = {
    "summary": "Регистрация нового пользователя",
    "description": "Создает нового пользователя с указанным email и паролем",
    "response_description": "Успешная регистрация",
    "responses": {
        200: {
            "description": "User registered successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "User registered",
                    },
                },
            },
        },
        400: {
            "model": err.DuplicateEmailResponse,
            "description": "Email already registered",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Email already registered",
                    },
                },
            },
        },
    },
}


login_schema = {
    "summary": "Аутентификация пользователя",
    "description": (
        "Аутентифицирует пользователя и возвращает access и refresh токены"
    ),
    "response_description": "Успешный вход",
    "responses": {
        200: {
            "description": "Successful login",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": (
                            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                        ),
                        "refresh_token": (
                            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                        ),
                        "token_type": "bearer",
                    },
                },
            },
        },
        400: {
            "model": err.InvalidCredentialsResponse,
            "description": "Invalid credentials",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid credentials",
                    },
                },
            },
        },
    },
}


refresh_schema = {
    "summary": "Обновление токенов",
    "description": (
        "Обновляет access и refresh токены "
        "используя существующий refresh токен"
    ),
    "response_description": "Новые токены",
    "responses": {
        200: {
            "description": "Tokens refreshed",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": (
                            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                        ),
                        "refresh_token": (
                            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                        ),
                        "token_type": "bearer",
                    },
                },
            },
        },
        401: {
            "model": err.RefreshTokenExpiredResponse,
            "description": "Refresh token expired or revoked",
            "content": {
                "application/json": {
                    "examples": {
                        "expired": {
                            "value": {
                                "detail": "Refresh token expired or revoked",
                            },
                        },
                        "invalid": {
                            "value": {
                                "detail": "Invalid refresh token",
                            },
                        },
                        "missing": {
                            "value": {
                                "detail": "Missing or invalid token format",
                            },
                        },
                    },
                },
            },
        },
    },
}


logout_schema = {
    "summary": "Выход пользователя",
    "description": "Отзывает все refresh токены пользователя",
    "response_description": "Успешный выход",
    "responses": {
        200: {
            "description": "Successfully logged out",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Successfully logged out",
                    },
                },
            },
        },
        401: {
            "model": err.InvalidTokenSignatureResponse,
            "description": "Invalid access token",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid": {
                            "value": {
                                "detail": "Invalid access token",
                            },
                        },
                        "missing": {
                            "value": {
                                "detail": "Missing or invalid token format",
                            },
                        },
                        "not_found": {
                            "value": {
                                "detail": "User not found",
                            },
                        },
                    },
                },
            },
        },
    },
}


change_credentials_schema = {
    "summary": "Изменение учетных данных",
    "description": "Обновляет email и/или пароль пользователя",
    "response_description": "Новый access токен",
    "responses": {
        200: {
            "description": "Credentials updated",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": (
                            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        ),
                        "token_type": "bearer",
                    },
                },
            },
        },
        400: {
            "model": err.ChangeCredentialsErrorResponse,
            "description": "Invalid old password or email already taken",
            "content": {
                "application/json": {
                    "examples": {
                        "password": {
                            "value": {
                                "detail": "Old password is incorrect",
                            },
                        },
                        "email": {
                            "value": {
                                "detail": "Email already registered",
                            },
                        },
                    },
                },
            },
        },
        401: {
            "model": err.InvalidTokenSignatureResponse,
            "description": "Invalid token",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid token",
                    },
                },
            },
        },
    },
}


login_history_schema = {
    "summary": "История входов",
    "description": "Возвращает историю входов пользователя",
    "response_description": "Список записей истории входов",
    "responses": {
        200: {
            "description": "Login history retrieved",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "login_time": "2023-06-15T10:30:00",
                            "ip_address": "192.168.1.1",
                            "action": "successfully login",
                        },
                    ],
                },
            },
        },
        401: {
            "model": err.InvalidTokenSignatureResponse,
            "description": "Invalid token",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid token",
                    },
                },
            },
        },
        404: {
            "model": err.NoLoginHistoryResponse,
            "description": "No login history found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "No login history found",
                    },
                },
            },
        },
    },
}

# Roles

create_role_schema = {
    "summary": "Создание новой роли",
    "description": "Создает новую роль (требуются права суперпользователя)",
    "response_description": "Созданная роль",
    "responses": {
        201: {
            "description": "Role created",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "admin",
                    },
                },
            },
        },
        400: {
            "description": "Role already exists",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Role admin already registered",
                    },
                },
            },
        },
        403: {
            "description": "Insufficient rights",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Insufficient rights",
                    },
                },
            },
        },
    },
}


roles_listing_schema = {
    "summary": "Список ролей",
    "description": (
        "Возвращает список ролей с фильтром по имени "
        "(требуются права суперпользователя)"
    ),
    "response_description": "Список ролей",
    "responses": {
        200: {
            "description": "Roles retrieved",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "name": "admin",
                        },
                    ],
                },
            },
        },
        403: {
            "description": "Insufficient rights",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Insufficient rights",
                    },
                },
            },
        },
    },
}


update_role_schema = {
    "summary": "Обновление роли",
    "description": (
        "Обновляет имя существующей роли "
        "(требуются права суперпользователя)"
    ),
    "response_description": "Обновленная роль",
    "responses": {
        200: {
            "description": "Role updated",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "moderator",
                    },
                },
            },
        },
        404: {
            "description": "Role not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Role not found",
                    },
                },
            },
        },
        403: {
            "description": "Insufficient rights",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Insufficient rights",
                    },
                },
            },
        },
    },
}


delete_role_schema = {
    "summary": "Удаление роли",
    "description": (
        "Удаляет существующую роль (требуются права суперпользователя)"
    ),
    "response_description": "Удаленная роль",
    "responses": {
        200: {
            "description": "Role deleted",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "admin",
                    },
                },
            },
        },
        404: {
            "description": "Role not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Role not found",
                    },
                },
            },
        },
        403: {
            "description": "Insufficient rights",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Insufficient rights",
                    },
                },
            },
        },
    },
}


assign_role_schema = {
    "summary": "Назначение роли пользователю",
    "description": (
        "Назначает роль пользователю по email "
        "(требуются права суперпользователя)"
    ),
    "response_description": "Пользователь с назначенной ролью",
    "responses": {
        200: {
            "description": "Role assigned",
            "content": {
                "application/json": {
                    "example": {
                        "email": "user@example.com",
                        "role": {
                            "id": 1,
                            "name": "admin",
                        },
                    },
                },
            },
        },
        404: {
            "description": "User or role not found",
            "content": {
                "application/json": {
                    "examples": {
                        "user": {
                            "value": {
                                "detail": "User not found",
                            },
                        },
                        "role": {
                            "value": {
                                "detail": "Role not found",
                            },
                        },
                    },
                },
            },
        },
        403: {
            "description": "Insufficient rights",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Insufficient rights",
                    },
                },
            },
        },
    },
}


unassign_role_schema = {
    "summary": "Снятие роли с пользователя",
    "description": (
        "Снимает роль с пользователя по email "
        "(требуются права суперпользователя)"
    ),
    "response_description": "Пользователь с удаленной ролью",
    "responses": {
        200: {
            "description": "Role unassigned",
            "content": {
                "application/json": {
                    "example": {
                        "email": "user@example.com",
                        "role": {
                            "id": 1,
                            "name": "admin",
                        },
                    },
                },
            },
        },
        404: {
            "description": "User, role or assignment not found",
            "content": {
                "application/json": {
                    "examples": {
                        "user": {
                            "value": {
                                "detail": "User not found",
                            },
                        },
                        "role": {
                            "value": {
                                "detail": "Role not found",
                            },
                        },
                        "assignment": {
                            "value": {
                                "detail": "User does not have that role",
                            },
                        },
                    },
                },
            },
        },
        403: {
            "description": "Insufficient rights",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Insufficient rights",
                    },
                },
            },
        },
    },
}

social_login_schema = {
    "summary": "Аутентификация через социальные сети",
    "description": "Аутентификация через Google ",
    "responses": {
        200: {
            "description": "Успешно",
        },
    },
}

social_callback_schema = {
    "summary": "Получение токена от провайдера",
    "description": "Получение токена от провайдера ",
    "responses": {
        200: {
            "description": "Role unassigned",
        },
    },
}
