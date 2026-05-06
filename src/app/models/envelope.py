import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.app.core.database import Base


class Envelope(Base):
    __tablename__ = "envelopes"
    __table_args__ = (UniqueConstraint("user_id", "set_id", "category_id", name="uq_envelope_user_set_cat"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[str] = mapped_column(String(20), ForeignKey("envelope_categories.id"), nullable=False)
    set_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("sets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    items_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    envelope_type: Mapped[str] = mapped_column(String(30), nullable=False, default="consumable")
    period: Mapped[str | None] = mapped_column(String(50), nullable=True)
    scale: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=Decimal("1.00"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
