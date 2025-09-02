from dotenv import dotenv_values

default_envs = {
    "DB_HOST": "theatre-db",
    "DB_PORT": 5432,
    "POSTGRES_DB": "theatre",
    "POSTGRES_USER": "postgres",
    "POSTGRES_PASSWORD": "secret",
    "AUTH_SECRET_KEY": "default_super_secret_key",
    "AUTH_ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRED_MINUTES": 10,
}


config = {
    **default_envs,
    **dotenv_values("/opt/common/.env"),
}
