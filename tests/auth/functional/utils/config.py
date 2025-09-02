from dotenv import dotenv_values

default_envs = {
    "DB_HOST": "theatre-db",
    "DB_PORT": 5432,
    "POSTGRES_DB": "theatre",
    "POSTGRES_USER": "postgres",
    "POSTGRES_PASSWORD": "secret",
    "AUTH_DB": "auth",
}


config = {
    **default_envs,
    **dotenv_values("/opt/tests/utils/.env"),
}
