from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.app.core.database import Base


class InventoryGroup(Base):
    __tablename__ = "inventory_groups"

    id: Mapped[str] = mapped_column(String(5), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)


class InventoryGroupCategory(Base):
    __tablename__ = "inventory_group_categories"

    group_id: Mapped[str] = mapped_column(String(5), ForeignKey("inventory_groups.id"), primary_key=True)
    category_id: Mapped[str] = mapped_column(String(20), ForeignKey("envelope_categories.id"), primary_key=True)
