import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.database import Base


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    article_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    category_id: Mapped[str | None] = mapped_column(String(20), ForeignKey("envelope_categories.id"), nullable=True)
    preview: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    views_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    likes_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dislikes_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    linked_set_id: Mapped[str | None] = mapped_column(
        String(20), ForeignKey("sets.id", ondelete="SET NULL"), nullable=True
    )
    linked_set_ids: Mapped[list[str] | None] = mapped_column(ARRAY(String(20)), nullable=True)
    is_private: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    read_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    blocks: Mapped[list["ArticleBlock"]] = relationship(
        back_populates="article",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ArticleBlock.position",
    )
    comments: Mapped[list["ArticleComment"]] = relationship(
        back_populates="article", cascade="all, delete-orphan", lazy="noload"
    )
    photos: Mapped[list["ArticlePhoto"]] = relationship(
        back_populates="article", cascade="all, delete-orphan", lazy="selectin"
    )
    author: Mapped["User | None"] = relationship(lazy="selectin", foreign_keys=[author_id])


class ArticleBlock(Base):
    __tablename__ = "article_blocks"
    __table_args__ = (UniqueConstraint("article_id", "position", name="uq_article_block_position"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    html: Mapped[str | None] = mapped_column(Text, nullable=True)
    items: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)

    article: Mapped["Article"] = relationship(back_populates="blocks")
