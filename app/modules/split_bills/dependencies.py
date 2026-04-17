from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.split_bills.models import SplitBill, SplitBillDebt
from app.modules.split_bills.service import get_bill_by_id

__all__ = ["get_owned_bill", "get_bill_debt"]


async def get_owned_bill(
    bill_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SplitBill:
    bill = await get_bill_by_id(db, bill_id)

    if bill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found",
        )

    if bill.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this bill",
        )

    return bill


async def get_bill_debt(
    bill_id: int,
    debt_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> tuple[SplitBill, SplitBillDebt]:

    bill = await get_owned_bill(bill_id, current_user, db)

    result = await db.execute(
        select(SplitBillDebt).where(
            SplitBillDebt.id == debt_id,
            SplitBillDebt.bill_id == bill.id,
        )
    )
    debt = result.scalar_one_or_none()

    if debt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Debt not found",
        )

    return bill, debt
