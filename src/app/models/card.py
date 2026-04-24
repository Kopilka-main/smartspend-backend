import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.app.core.database import Base


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    bank_color: Mapped[str] = mapped_column(String(7), nullable=False)
    bank_text_color: Mapped[str] = mapped_column(String(7), nullable=False, default="#FFF")
    bank_abbr: Mapped[str | None] = mapped_column(String(5), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    card_type: Mapped[str] = mapped_column(String(20), nullable=False)
    cashback: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    cashback_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    grace_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fee: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fee_base: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_systemic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    conditions: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    bonus_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bonus_system: Mapped[str | None] = mapped_column(String(200), nullable=True)
    bonus_desc: Mapped[str | None] = mapped_column(Text, nullable=True)
    fee_desc: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserCard(Base):
    __tablename__ = "user_cards"
    __table_args__ = (UniqueConstraint("user_id", "card_id", name="uq_user_card"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    card_id: Mapped[str] = mapped_column(String(20), ForeignKey("cards.id", ondelete="CASCADE"), nullable=False)
    spending: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
