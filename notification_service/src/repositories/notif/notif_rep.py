from notification_service.src.db.postgres import db_helper
from notification_service.src.models.notif.db_models import Notification
from notification_service.src.repositories.sqlalchemy_repository import (
    SqlAlchemyRepository,
)
from notification_service.src.schemas.notif.notif import (
    NotificationCreate,
    NotificationUpdate,
)


class NotificationRepository(
    SqlAlchemyRepository[Notification, NotificationCreate, NotificationUpdate],
):
    pass


def get_notification_repository():
    return NotificationRepository(
        model=Notification,
        db_session=db_helper.get_db_session,
    )
