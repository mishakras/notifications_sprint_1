from auth_service.src.db.postgres import db_helper
from auth_service.src.models.auth.db_models import RefreshToken
from auth_service.src.repositories.sqlalchemy_repository import (
    SqlAlchemyRepository,
)
from auth_service.src.schemas.auth.refresh_token import (
    RefreshTokenCreate,
    RefreshTokenUpdate,
)


class RefreshTokenRepository(
    SqlAlchemyRepository[RefreshToken, RefreshTokenCreate, RefreshTokenUpdate],
):
    pass


refresh_token_repository = RefreshTokenRepository(
    model=RefreshToken,
    db_session=db_helper.get_db_session,
)
