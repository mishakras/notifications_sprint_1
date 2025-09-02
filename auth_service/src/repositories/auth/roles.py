from auth_service.src.db.postgres import db_helper
from auth_service.src.models.auth.db_models import Role
from auth_service.src.repositories.sqlalchemy_repository import (
    SqlAlchemyRepository,
)
from auth_service.src.schemas.auth.roles import RoleCreate, RoleUpdate


class RoleRepository(
    SqlAlchemyRepository[Role, RoleCreate, RoleUpdate],
):
    pass


role_repository = RoleRepository(
    model=Role,
    db_session=db_helper.get_db_session,
)
