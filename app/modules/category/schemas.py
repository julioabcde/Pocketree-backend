from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from app.modules.category.models import CategoryType


__all__ = [
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryResponse",
]


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: CategoryType
    icon: str = Field(default="", max_length=50)
    color: str = Field(default="#808080", max_length=7)
    parent_id: int | None = None

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str) -> str:
        value = value.strip()
        if not value.startswith("#") or len(value) != 7:
            raise ValueError("Color must be in the format #RRGGBB")
        try:
            int(value[1:], 16)
        except ValueError:
            raise ValueError("Color must be a valid hexadecimal value")
        return value.upper()


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    icon: str | None = Field(default=None, max_length=50)
    color: str | None = Field(default=None, max_length=7)

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, value: str) -> str:
        if value is None:
            return value
        return " ".join(value.split())

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str) -> str:
        if value is None:
            return value
        value = value.strip()
        if not value.startswith("#") or len(value) != 7:
            raise ValueError("Color must be in the format #RRGGBB")
        try:
            int(value[1:], 16)
        except ValueError:
            raise ValueError("Color must be a valid hexadecimal value")
        return value.upper()


class CategoryResponse(BaseModel):
    id: int
    name: str
    type: CategoryType
    icon: str
    color: str
    parent_id: int | None
    is_system: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
