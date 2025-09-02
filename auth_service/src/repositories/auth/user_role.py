from auth_service.src.db.postgres import db_helper
from auth_service.src.models.auth.db_models import UserRole
from auth_service.src.repositories.sqlalchemy_repository import (
    SqlAlchemyRepository,
)
from auth_service.src.schemas.auth.users_roles import (
    UserRoleCreate,
    UserRoleUpdate,
)


class UserRoleRepository(
    SqlAlchemyRepository[UserRole, UserRoleCreate, UserRoleUpdate],
):
    pass


user_role_repository = UserRoleRepository(
    model=UserRole,
    db_session=db_helper.get_db_session,
)
