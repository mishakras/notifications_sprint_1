from sqlalchemy import JSON, Boolean, Column, String, Text
from sqlalchemy.dialects.postgresql import UUID
from src.db.postgres import Base


class Template(Base):
    __tablename__ = "templates"
    __table_args__ = {"schema": "notifications"}

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    subject = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    notification_type = Column(String(20), nullable=False)  # email, sms, push
    is_active = Column(Boolean, default=True)
    variables = Column(JSON)  # Описание переменных для шаблона

    def __repr__(self):
        return f"<Template {self.name}>"
