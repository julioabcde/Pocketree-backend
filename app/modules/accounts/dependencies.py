from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.accounts.models import Account
from app.modules.accounts.service import get_account_by_id
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User


__all__ = [
    "get_owned_account",
]

async def get_owned_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Account:
    account = await get_account_by_id(db, account_id)
    
    if account is None:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
        
    if account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this account",
        )
    
    return