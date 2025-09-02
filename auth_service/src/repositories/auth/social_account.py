from auth_service.src.db.postgres import db_helper
from auth_service.src.models.auth.db_models import SocialAccount
from auth_service.src.repositories.sqlalchemy_repository import (
    SqlAlchemyRepository,
)
from auth_service.src.schemas.auth.social_account import (
    SocialAccountCreate,
    SocialAccountUpdate,
)


class SocialAccountRepository(
    SqlAlchemyRepository[
        SocialAccount,
        SocialAccountCreate,
        SocialAccountUpdate,
    ],
):
    pass


social_account_repository = SocialAccountRepository(
    model=SocialAccount,
    db_session=db_helper.get_db_session,
)
