from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.app.core.database import Base


class Deposit(Base):
    __tablename__ = "deposits"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    bank_color: Mapped[str] = mapped_column(String(7), nullable=False)
    bank_text_color: Mapped[str] = mapped_column(String(7), nullable=False, default="#FFF")
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    rates: Mapped[dict] = mapped_column(JSONB, nullable=False)
    min_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    replenishment: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    withdrawal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    freq: Mapped[str] = mapped_column(String(20), nullable=False, default="end")
    is_systemic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    conditions: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    conditions_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    params: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
