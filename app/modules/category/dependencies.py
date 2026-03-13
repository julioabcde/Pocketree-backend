from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.category.models import Category
from app.modules.category.service import get_category_by_id
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User

__all__ = ["get_visible_category", "get_editable_category"]


async def get_visible_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Category:
    category = await get_category_by_id(db, category_id)

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    is_system = category.user_id is None
    is_owner = category.user_id == current_user.id

    if not is_system and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this category",
        )

    return category


async def get_editable_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Category:
    category = await get_category_by_id(db, category_id)

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    if category.is_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System categories cannot be edited",
        )

    if category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit this category",
        )

    return category
