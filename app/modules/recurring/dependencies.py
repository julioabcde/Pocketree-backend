from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.recurring.models import RecurringTransaction
from app.modules.recurring.service import get_recurring_by_id

__all__ = ["get_owned_recurring"]


async def get_owned_recurring(
    recurring_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecurringTransaction:
    recurring = await get_recurring_by_id(db, recurring_id)

    if recurring is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring transaction not found",
        )

    if recurring.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this recurring transaction",
        )

    return recurring
