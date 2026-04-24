import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.core.database import Base


class UserFinance(Base):
    __tablename__ = "user_finance"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    income: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    housing: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    credit: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    credit_months: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    capital: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    emo_rate: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False, default=Decimal("0.05"))
    card_spending: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="finance")
