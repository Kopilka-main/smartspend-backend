import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.database import Base
from src.app.models.enums import Theme, UserStatus


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    username: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True, index=True)
    initials: Mapped[str] = mapped_column(String(2), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#7DAF92")
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[UserStatus] = mapped_column(String(20), nullable=False, default=UserStatus.UNVERIFIED)
    theme: Mapped[Theme] = mapped_column(String(5), nullable=False, default=Theme.LIGHT)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="Europe/Moscow")
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notify_new_sets: Mapped[bool] = mapped_column(nullable=False, server_default="true", default=True)
    notify_author_articles: Mapped[bool] = mapped_column(nullable=False, server_default="true", default=True)
    notify_subscriptions: Mapped[bool] = mapped_column(nullable=False, server_default="true", default=True)
    notify_set_changes: Mapped[bool] = mapped_column(nullable=False, server_default="true", default=True)
    notify_reminders: Mapped[bool] = mapped_column(nullable=False, server_default="true", default=True)
    privacy_sets: Mapped[str] = mapped_column(String(20), nullable=False, default="all")
    privacy_articles: Mapped[str] = mapped_column(String(20), nullable=False, default="all")
    privacy_profile: Mapped[str] = mapped_column(String(20), nullable=False, default="all")
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    oauth_provider: Mapped[str | None] = mapped_column(String(20), nullable=True)
    oauth_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    finance: Mapped["UserFinance | None"] = relationship(back_populates="user", uselist=False, lazy="selectin")
