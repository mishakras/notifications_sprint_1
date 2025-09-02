from sqlalchemy import UUID, Boolean, Column, MetaData, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID, primary_key=True, index=True)
    hashed = Column(String, nullable=False)
    is_sent = Column(Boolean, default=False)

    meta = MetaData(schema="notifications")
    __table_args__ = {"schema": "notifications"}
