from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from src.db.postgres import Base


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = {"schema": "notifications"}

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    template_id = Column(String(100), nullable=False)
    notification_type = Column(String(20), nullable=False)  # email, sms, push
    subject = Column(Text)
    body = Column(Text)
    status = Column(String(20), default="pending")  # pending, sent, failed
    retry_count = Column(Integer, default=0)
    metadata = Column(JSON)  # Дополнительные данные
    created_at = Column(DateTime, server_default=func.now())
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Notification {self.id} for user {self.user_id}>"
