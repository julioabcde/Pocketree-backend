"""add split bill participant items table

Revision ID: f6b9b8f3c3e1
Revises: ae8a8c8c44b3
Create Date: 2026-04-03 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6b9b8f3c3e1"
down_revision: Union[str, Sequence[str], None] = "ae8a8c8c44b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "split_bill_participant_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bill_id", sa.Integer(), nullable=False),
        sa.Column("participant_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("portion", sa.Integer(), nullable=False),
        sa.Column(
            "allocated_subtotal",
            sa.Numeric(precision=15, scale=2),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "portion > 0",
            name="ck_split_bill_participant_items_portion_positive",
        ),
        sa.CheckConstraint(
            "allocated_subtotal >= 0",
            name="ck_split_bill_participant_items_allocated_non_negative",
        ),
        sa.ForeignKeyConstraint(
            ["bill_id"], ["split_bills.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["participant_id"],
            ["split_bill_participants.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["item_id"], ["split_bill_items.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "participant_id",
            "item_id",
            name="uq_split_bill_participant_items_participant_item",
        ),
    )

    op.create_index(
        op.f("ix_split_bill_participant_items_id"),
        "split_bill_participant_items",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_split_bill_participant_items_bill_id"),
        "split_bill_participant_items",
        ["bill_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_split_bill_participant_items_participant_id"),
        "split_bill_participant_items",
        ["participant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_split_bill_participant_items_item_id"),
        "split_bill_participant_items",
        ["item_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_split_bill_participant_items_item_id"),
        table_name="split_bill_participant_items",
    )
    op.drop_index(
        op.f("ix_split_bill_participant_items_participant_id"),
        table_name="split_bill_participant_items",
    )
    op.drop_index(
        op.f("ix_split_bill_participant_items_bill_id"),
        table_name="split_bill_participant_items",
    )
    op.drop_index(
        op.f("ix_split_bill_participant_items_id"),
        table_name="split_bill_participant_items",
    )
    op.drop_table("split_bill_participant_items")
