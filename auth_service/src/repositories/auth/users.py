from sqlalchemy import select

from auth_service.src.auth.exceptions import UserNotFoundException
from auth_service.src.db.postgres import db_helper
from auth_service.src.models.auth.db_models import User
from auth_service.src.repositories.sqlalchemy_repository import (
    SqlAlchemyRepository,
)
from auth_service.src.schemas.auth.users import UserCreate, UserUpdate


class UserRepository(SqlAlchemyRepository[User, UserCreate, UserUpdate]):
    async def get_user_roles(self, user_email):
        async with self.db_session() as session:
            user = await session.execute(
                select(User).filter_by(user_email=user_email),
            )
            if not user:
                raise UserNotFoundException
            roles = []
            for role_to_user in user.roles:
                roles.extend(role_to_user.role)
            return roles


user_repository = UserRepository(
    model=User,
    db_session=db_helper.get_db_session,
)
