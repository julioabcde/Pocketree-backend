from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.accounts.dependencies import get_owned_account
from app.modules.accounts.models import Account
from app.modules.accounts.schemas import (
    AccountCreate,
    AccountResponse,
    AccountSummary,
    AccountUpdate,
)
from app.modules.accounts.service import (
    create_account,
    get_accounts_by_user,
    get_account_summary,
    soft_delete_account,
    update_account,
)
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User

router = APIRouter(prefix="/accounts", tags=["Accounts"])

# TODO: 
# 1. 
# Check /accounts endpoint. Currently it returns empty array even if there are accounts in the database
# This is because the get_accounts_by_user function is filtering by user_id, but the user_id is not being set when creating an account.
# Need to set the user_id when creating an account and also make sure that the user_id
# is being passed correctly to the get_accounts_by_user function.
# Also need to check the get_account_summary function to make sure it is calculating the total balance and accounts count correctly.
# Finally, need to check the get_owned_account dependency to make sure it is checking the ownership of the account correctly.
# 2. 
# Add unique constraint on account name per user.
# This will prevent users from creating multiple accounts with the same name, which can cause confusion when listing accounts and calculating summaries.


@router.post(
    "",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create(
    data: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await create_account(db, current_user.id, data)
    return account


@router.get(
    "",
    response_model=list[AccountResponse],
)
async def list_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    accounts = await get_accounts_by_user(db, current_user.id)
    return accounts


@router.get(
    "/summary",
    response_model=AccountSummary,
)
async def summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await get_account_summary(db, current_user.id)
    return result


@router.get(
    "/{account_id}",
    response_model=AccountResponse,
)
async def detail(
    account: Account = Depends(get_owned_account),
):
    return account

@router.put(
    "/{account_id}",
    response_model=AccountResponse,
)
async def update(
    data: AccountUpdate,
    account: Account = Depends(get_owned_account),
    db: AsyncSession = Depends(get_db),
):
    updated = await update_account(db, account, data)
    return updated

@router.delete(
    "/{account_id}",
)
async def delete(
    account: Account = Depends(get_owned_account),
    db: AsyncSession = Depends(get_db),
):
    await soft_delete_account(db, account)
    return {"message": "Account deleted successfully"}