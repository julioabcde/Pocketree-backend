from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.category.models import Category, CategoryType
from app.modules.category.schemas import CategoryCreate, CategoryUpdate

__all__ = [
    "create_category",
    "get_category_by_id",
    "get_categories_by_user",
    "get_children_count",
    "update_category",
    "soft_delete_category",
    "check_duplicate_category",
    "seed_default_categories",
]


async def check_duplicate_category(
    db: AsyncSession,
    user_id: int,
    name: str,
    category_type: CategoryType,
    parent_id: int | None = None,
    exclude_id: int | None = None,
) -> str | None:

    base_query = select(Category).where(
        or_(Category.user_id.is_(None), Category.user_id == user_id),
        func.lower(Category.name) == name.lower(),
        Category.type == category_type,
        ~Category.is_deleted,
    )

    sibling_query = base_query

    if parent_id is not None:
        sibling_query = sibling_query.where(Category.parent_id == parent_id)
    else:
        sibling_query = sibling_query.where(Category.parent_id.is_(None))

    if exclude_id is not None:
        sibling_query = sibling_query.where(Category.id != exclude_id)

    result = await db.execute(sibling_query)
    if result.scalars().first() is not None:
        return "A category with this name already exists"

    if parent_id is not None:
        parent_query = base_query.where(Category.parent_id.is_(None))

        if exclude_id is not None:
            parent_query = parent_query.where(Category.id != exclude_id)

        result = await db.execute(parent_query)
        if result.scalars().first() is not None:
            return (
                "Subcategory name cannot match an existing "
                "top-level category name"
            )

    return None


async def create_category(
    db: AsyncSession,
    data: CategoryCreate,
    user_id: int,
) -> Category:
    if data.parent_id is not None:
        parent = await get_category_by_id(db, data.parent_id)

        if parent is None:
            raise ValueError("Parent category not found")

        if parent.user_id not in (None, user_id):
            raise ValueError("Invalid parent category")

        if parent.is_subcategory:
            raise ValueError("Cannot assign a subcategory as a parent")

        if parent.type != data.type:
            raise ValueError(
                f"Child type must match parent type "
                f"parent is {parent.type.value}"
            )

    category = Category(
        user_id=user_id,
        parent_id=data.parent_id,
        name=data.name,
        type=data.type,
        icon=data.icon,
        color=data.color,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def get_category_by_id(
    db: AsyncSession, category_id: int
) -> Category | None:
    result = await db.execute(
        select(Category).where(
            Category.id == category_id,
            ~Category.is_deleted,
        )
    )
    return result.scalars_one_or_none()


async def get_categories_by_user(
    db: AsyncSession,
    user_id: int,
    category_type: CategoryType | None = None,
    parent_id: int | None = None,
) -> list[Category]:
    query = select(Category).where(
        or_(Category.user_id.is_(None), Category.user_id == user_id),
        ~Category.is_deleted,
    )

    if category_type is not None:
        query = query.where(Category.type == category_type)

    if parent_id is not None:
        query = query.where(Category.parent_id == parent_id)
    else:
        query = query.where(Category.parent_id.is_(None))

    query = query.order_by(Category.is_system.desc(), Category.name)

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_children_count(db: AsyncSession, category_id: int) -> int:
    result = await db.execute(
        select(func.count(Category.id)).where(
            Category.parent_id == category_id,
            ~Category.is_deleted,
        )
    )
    return result.scalar_one()


async def update_category(
    db: AsyncSession, category: Category, data: CategoryUpdate
) -> Category:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    await db.commit()
    await db.refresh(category)
    return category


async def soft_delete_category(
    db: AsyncSession, category: Category
) -> Category:
    category.is_deleted = True
    category.deleted_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(category)
    return category


async def seed_default_categories(db: AsyncSession) -> None:
    from app.modules.category.models import DEFAULT_CATEGORIES

    existing = await db.execute(
        select(func.count(Category.id)).where(
            Category.is_system.is_(True),
        )
    )
    if existing.scalar_one() > 0:
        return

    for category_data in DEFAULT_CATEGORIES:
        category = Category(
            user_id=None,
            parent_id=None,
            name=category_data["name"],
            type=CategoryType(category_data["type"]),
            icon=category_data["icon"],
            color=category_data["color"],
            is_system=True,
        )
        db.add(category)

    await db.commit()
