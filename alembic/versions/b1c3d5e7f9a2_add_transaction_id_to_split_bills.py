"""add transaction_id to split bills and settlements, user_id to participants

Revision ID: b1c3d5e7f9a2
Revises: f6b9b8f3c3e1
Create Date: 2026-04-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b1c3d5e7f9a2"
down_revision: Union[str, Sequence[str], None] = "f6b9b8f3c3e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "split_bills",
        sa.Column(
            "transaction_id",
            sa.Integer(),
            sa.ForeignKey("transactions.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "split_bill_settlements",
        sa.Column(
            "transaction_id",
            sa.Integer(),
            sa.ForeignKey("transactions.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "split_bill_participants",
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("split_bill_participants", "user_id")
    op.drop_column("split_bill_settlements", "transaction_id")
    op.drop_column("split_bills", "transaction_id")
