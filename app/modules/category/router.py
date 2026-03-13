from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.category.dependencies import (
    get_editable_category,
    get_visible_category,
)
from app.modules.category.models import Category, CategoryType
from app.modules.category.schemas import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)
from app.modules.category.service import (
    check_duplicate_category,
    create_category,
    get_categories_by_user,
    get_children_count,
    soft_delete_category,
    update_category,
)
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create(
    data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    duplicate_reason = await check_duplicate_category(
        db,
        current_user.id,
        data.name,
        data.type,
        parent_id=data.parent_id,
    )
    if duplicate_reason is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=duplicate_reason,
        )

    try:
        category = await create_category(db, data, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid parent category",
        )

    return category


@router.get(
    "",
    response_model=list[CategoryResponse],
)
async def list_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    type: CategoryType | None = Query(
        default=None,
        description="Filter by income or expense",
    ),
    parent_id: int | None = Query(
        default=None,
        description="Get subcategories of this parent. "
        "Omit to get top-level categories only.",
    ),
):
    categories = await get_categories_by_user(
        db, current_user.id, category_type=type, parent_id=parent_id
    )
    return categories


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
)
async def detail(
    category: Category = Depends(get_visible_category),
):
    return category


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
)
async def update(
    data: CategoryUpdate,
    category: Category = Depends(get_editable_category),
    db: AsyncSession = Depends(get_db),
):
    if data.name is not None and data.name.lower() != category.name.lower():
        duplicate_reason = await check_duplicate_category(
            db,
            category.user_id,
            data.name,
            category.type,
            parent_id=category.parent_id,
            exclude_id=category.id,
        )
        if duplicate_reason is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=duplicate_reason,
            )

    try:
        updated = await update_category(db, category, data)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A category with this name already exists",
        )

    return updated


@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
async def delete(
    category: Category = Depends(get_editable_category),
    db: AsyncSession = Depends(get_db),
):
    if category.is_parent:
        children = await get_children_count(db, category.id)
        if children > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot delete category with "
                f"{children} active subcategories. "
                f"Delete subcategories first.",
            )

    await soft_delete_category(db, category)
    return {"message": "Category deleted successfully"}
