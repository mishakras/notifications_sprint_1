import asyncio

import typer
from typing_extensions import Annotated

from auth_service.src.auth.auth import hash_password
from auth_service.src.repositories.auth.users import user_repository
from auth_service.src.schemas.auth.users import UserCreate

app = typer.Typer()


@app.command()
def create_super_user(
    email: Annotated[
        str,
        typer.Option(prompt=True),
    ],
    password: Annotated[
        str,
        typer.Option(prompt=True, hide_input=True),
    ],
):
    async def create():
        try:
            new_user = UserCreate(
                email=email,
                hashed_password=hash_password(password),
                is_superuser=True,
            )

            await user_repository.create(data=new_user.model_dump())
            typer.echo(f"User created {new_user.email}")
        except Exception as e:
            typer.echo(e)

    asyncio.run(create())


if __name__ == "__main__":
    app()
