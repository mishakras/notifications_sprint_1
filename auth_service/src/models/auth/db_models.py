import datetime

from sqlalchemy import (
    UUID,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_superuser = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime,
        default=datetime.datetime.now(),
        nullable=False,
    )
    updated_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)

    roles = relationship("UserRole", back_populates="user")
    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    login_histories = relationship(
        "LoginHistory",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    token_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    refresh_token = Column(String(255), nullable=False)
    issued_at = Column(DateTime, server_default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="refresh_tokens")


class LoginHistory(Base):
    __tablename__ = "login_history"

    entry_id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    login_time = Column(DateTime, server_default=func.now(), nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    action = Column(String(50), nullable=False)

    user = relationship("User", back_populates="login_histories")

    __table_args__ = (
        PrimaryKeyConstraint("entry_id", "login_time"),
        {"postgresql_partition_by": "RANGE (login_time)"},
    )


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)

    user = relationship("User", back_populates="roles")
    role = relationship("Role")


class SocialAccount(Base):
    __tablename__ = "social_account"

    id = Column(UUID(as_uuid=True), primary_key=True)
    social_id = Column(Text, nullable=False)
    social_name = Column(Text, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship(User, backref=backref("social_accounts", lazy=True))

    __table_args__ = (
        UniqueConstraint("social_id", "social_name", name="social_pk"),
    )

    def __repr__(self):
        return f"<SocialAccount {self.social_name}:{self.user_id}>"
