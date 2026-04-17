"""add reporting indexes for transactions

Revision ID: 9c1f2d6a7b4e
Revises: b1c3d5e7f9a2
Create Date: 2026-04-11 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9c1f2d6a7b4e"
down_revision: Union[str, Sequence[str], None] = "b1c3d5e7f9a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_tx_reports_user_date_active_non_transfer",
        "transactions",
        ["user_id", "date"],
        unique=False,
        postgresql_where=sa.text("is_deleted = false AND transfer_id IS NULL"),
    )

    op.create_index(
        "ix_tx_reports_user_account_date_active_non_transfer",
        "transactions",
        ["user_id", "account_id", "date"],
        unique=False,
        postgresql_where=sa.text("is_deleted = false AND transfer_id IS NULL"),
    )

    op.create_index(
        "ix_tx_reports_user_type_date_amount_active_non_transfer",
        "transactions",
        ["user_id", "type", "date", sa.text("amount DESC")],
        unique=False,
        postgresql_where=sa.text("is_deleted = false AND transfer_id IS NULL"),
    )

    op.create_index(
        "ix_tx_reports_user_category_date_active_non_transfer",
        "transactions",
        ["user_id", "category_id", "date"],
        unique=False,
        postgresql_where=sa.text("is_deleted = false AND transfer_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_tx_reports_user_category_date_active_non_transfer",
        table_name="transactions",
        postgresql_where=sa.text("is_deleted = false AND transfer_id IS NULL"),
    )

    op.drop_index(
        "ix_tx_reports_user_type_date_amount_active_non_transfer",
        table_name="transactions",
        postgresql_where=sa.text("is_deleted = false AND transfer_id IS NULL"),
    )
    op.drop_index(
        "ix_tx_reports_user_account_date_active_non_transfer",
        table_name="transactions",
        postgresql_where=sa.text("is_deleted = false AND transfer_id IS NULL"),
    )
    op.drop_index(
        "ix_tx_reports_user_date_active_non_transfer",
        table_name="transactions",
        postgresql_where=sa.text("is_deleted = false AND transfer_id IS NULL"),
    )
