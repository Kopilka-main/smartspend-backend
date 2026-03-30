from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.app.core.database import Base


class EnvelopeCategory(Base):
    __tablename__ = "envelope_categories"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)
