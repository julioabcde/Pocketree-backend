import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.db.mixins import TimestampMixin

__all__ = ["Category", "CategoryType", "DEFAULT_CATEGORIES"]


class CategoryType(str, enum.Enum):
    income = "income"
    expense = "expense"


DEFAULT_CATEGORIES: list[dict] = [
    # Expense
    {"name": "Food", "type": "expense", "icon": "🍔", "color": "#FF6B35"},
    {"name": "Transport", "type": "expense", "icon": "🚗", "color": "#4ECDC4"},
    {"name": "Shopping", "type": "expense", "icon": "🛍️", "color": "#FF69B4"},
    {"name": "Bills", "type": "expense", "icon": "📄", "color": "#95E1D3"},
    {
        "name": "Entertainment",
        "type": "expense",
        "icon": "🎮",
        "color": "#F38181",
    },
    {"name": "Health", "type": "expense", "icon": "💊", "color": "#3DDC84"},
    {"name": "Education", "type": "expense", "icon": "📚", "color": "#7C83FD"},
    {"name": "Pets", "type": "expense", "icon": "🐾", "color": "#A8D8EA"},
    # Income
    {"name": "Salary", "type": "income", "icon": "💰", "color": "#2ECC71"},
    {"name": "Freelance", "type": "income", "icon": "💻", "color": "#3498DB"},
    {"name": "Investment", "type": "income", "icon": "📈", "color": "#F39C12"},
    {"name": "Gift", "type": "income", "icon": "🎁", "color": "#E74C3C"},
]


class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    __table_args__ = (
        Index(
            "ix_categories_unique_active",
            "user_id",
            text("LOWER(name)"),
            "type",
            "parent_id",
            unique=True,
            postgresql_where=text("is_deleted = false"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )

    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=True, index=True
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    type: Mapped[CategoryType] = mapped_column(
        SAEnum(CategoryType , name="category_type"), nullable=False
    )

    icon: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    color: Mapped[str] = mapped_column(
        String(7), nullable=False, default="#808080"
    )

    is_system: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    @property
    def is_parent(self) -> bool:
        return self.parent_id is None

    @property
    def is_subcategory(self) -> bool:
        return self.parent_id is not None

    def __repr__(self) -> str:
        return (
            f"<Category(id={self.id}, name={self.name!r}, "
            f"type={self.type.value}, parent_id={self.parent_id})>"
        )
