from auth_service.src.db.postgres import db_helper
from auth_service.src.models.auth.db_models import LoginHistory
from auth_service.src.repositories.sqlalchemy_repository import (
    SqlAlchemyRepository,
)
from auth_service.src.schemas.auth.history import HistoryCreate, HistoryUpdate


class HistoryRepository(
    SqlAlchemyRepository[LoginHistory, HistoryCreate, HistoryUpdate],
):
    pass


history_repository = HistoryRepository(
    model=LoginHistory,
    db_session=db_helper.get_db_session,
)
