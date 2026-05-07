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
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.database import Base


class InventoryItem(Base):
    __tablename__ = "inventory_items"
    __table_args__: tuple = ()

    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    group_id: Mapped[str] = mapped_column(String(20), ForeignKey("inventory_groups.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    set_id: Mapped[str | None] = mapped_column(String(20), ForeignKey("sets.id", ondelete="SET NULL"), nullable=True)
    is_extra: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    paused: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    qty: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    daily_use: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    last_bought: Mapped[date | None] = mapped_column(Date, nullable=True)
    wear_life_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    wear_life: Mapped[int | None] = mapped_column(Integer, nullable=True)
    wear_life_unit: Mapped[str | None] = mapped_column(String(10), nullable=True)
    use_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    use_period: Mapped[str | None] = mapped_column(String(10), nullable=True)
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    base_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    period_years: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    purchases: Mapped[list["InventoryPurchase"]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="InventoryPurchase.position",
    )
    photos: Mapped[list["InventoryPhoto"]] = relationship(
        back_populates="item", cascade="all, delete-orphan", lazy="selectin"
    )


class InventoryPurchase(Base):
    __tablename__ = "inventory_purchases"
    __table_args__ = (UniqueConstraint("item_id", "position", name="uq_purchase_item_pos"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[str] = mapped_column(
        String(60), ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    bought: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    item: Mapped["InventoryItem"] = relationship(back_populates="purchases")


class InventoryPhoto(Base):
    __tablename__ = "inventory_photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[str] = mapped_column(
        String(60), ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    item: Mapped["InventoryItem"] = relationship(back_populates="photos")
