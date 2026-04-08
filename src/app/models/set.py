import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.database import Base


class Set(Base):
    __tablename__ = "sets"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    category_id: Mapped[str] = mapped_column(String(20), ForeignKey("envelope_categories.id"), nullable=False)
    set_type: Mapped[str] = mapped_column(String(20), nullable=False, default="base")
    color: Mapped[str] = mapped_column(String(7), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    amount_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    users_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    added: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_private: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    about_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    about_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    items: Mapped[list["SetItem"]] = relationship(back_populates="set", cascade="all, delete-orphan", lazy="selectin")
    comments: Mapped[list["SetComment"]] = relationship(
        back_populates="set", cascade="all, delete-orphan", lazy="noload"
    )
    author: Mapped["User | None"] = relationship(lazy="selectin", foreign_keys=[author_id])


class SetItem(Base):
    __tablename__ = "set_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    set_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("sets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    note: Mapped[str | None] = mapped_column(String(200), nullable=True)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False, default="consumable")
    price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    qty: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    daily_use: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    wear_life_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    planned_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    base_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    period_years: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    set: Mapped["Set"] = relationship(back_populates="items")
