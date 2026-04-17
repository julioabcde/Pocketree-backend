"""create split bills tables

Revision ID: c729b6565cf2
Revises: 8d2ffeae9ad0
Create Date: 2026-03-26 01:13:53.721161

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c729b6565cf2'
down_revision: Union[str, Sequence[str], None] = '8d2ffeae9ad0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Parent table
    op.create_table('split_bills',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('subtotal', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('total_amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('receipt_image_url', sa.String(length=500), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_split_bills_id'), 'split_bills', ['id'], unique=False)
    op.create_index(
        'ix_split_bills_user_active',
        'split_bills', ['user_id'],
        unique=False,
        postgresql_where=sa.text('is_deleted = false'),
    )

    # Charges 
    op.create_table('split_bill_charges',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('bill_id', sa.Integer(), nullable=False),
    sa.Column('type', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('amount > 0', name='ck_split_bill_charges_amount_positive'),
    sa.ForeignKeyConstraint(['bill_id'], ['split_bills.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_split_bill_charges_id'), 'split_bill_charges', ['id'], unique=False)
    op.create_index(op.f('ix_split_bill_charges_bill_id'), 'split_bill_charges', ['bill_id'], unique=False)

    # Items
    op.create_table('split_bill_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('bill_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('price', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('subtotal', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('price > 0', name='ck_split_bill_items_price_positive'),
    sa.CheckConstraint('quantity > 0', name='ck_split_bill_items_quantity_positive'),
    sa.CheckConstraint('subtotal >= 0', name='ck_split_bill_items_subtotal_non_negative'),
    sa.ForeignKeyConstraint(['bill_id'], ['split_bills.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_split_bill_items_id'), 'split_bill_items', ['id'], unique=False)
    op.create_index(op.f('ix_split_bill_items_bill_id'), 'split_bill_items', ['bill_id'], unique=False)

    # Participants
    op.create_table('split_bill_participants',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('bill_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('is_payer', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    sa.Column('paid_amount', sa.Numeric(precision=15, scale=2), nullable=False, server_default=sa.text('0')),
    sa.Column('final_amount', sa.Numeric(precision=15, scale=2), nullable=False, server_default=sa.text('0')),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['bill_id'], ['split_bills.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_split_bill_participants_id'), 'split_bill_participants', ['id'], unique=False)
    op.create_index(op.f('ix_split_bill_participants_bill_id'), 'split_bill_participants', ['bill_id'], unique=False)

    # Debts 
    op.create_table('split_bill_debts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('bill_id', sa.Integer(), nullable=False),
    sa.Column('debtor_participant_id', sa.Integer(), nullable=False),
    sa.Column('creditor_participant_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('remaining_amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['bill_id'], ['split_bills.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['debtor_participant_id'], ['split_bill_participants.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['creditor_participant_id'], ['split_bill_participants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.CheckConstraint('amount > 0', name='ck_split_bill_debts_amount_positive'),
    sa.CheckConstraint('remaining_amount >= 0', name='ck_split_bill_debts_remaining_not_negative'),
    sa.CheckConstraint('remaining_amount <= amount', name='ck_split_bill_debts_remaining_not_exceed'),
    )
    op.create_index(op.f('ix_split_bill_debts_id'), 'split_bill_debts', ['id'], unique=False)
    op.create_index(op.f('ix_split_bill_debts_bill_id'), 'split_bill_debts', ['bill_id'], unique=False)
    op.create_index(
        'ix_split_bill_debts_bill_debtor',
        'split_bill_debts',
        ['bill_id', 'debtor_participant_id'],
        unique=False,
    )

    # Settlements 
    op.create_table('split_bill_settlements',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('bill_id', sa.Integer(), nullable=False),
    sa.Column('debt_id', sa.Integer(), nullable=False),
    sa.Column('from_participant_id', sa.Integer(), nullable=False),
    sa.Column('to_participant_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['bill_id'], ['split_bills.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['debt_id'], ['split_bill_debts.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['from_participant_id'], ['split_bill_participants.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['to_participant_id'], ['split_bill_participants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.CheckConstraint('amount > 0', name='ck_split_bill_settlements_amount_positive'),
    )
    op.create_index(op.f('ix_split_bill_settlements_id'), 'split_bill_settlements', ['id'], unique=False)
    op.create_index(op.f('ix_split_bill_settlements_bill_id'), 'split_bill_settlements', ['bill_id'], unique=False)
    op.create_index(op.f('ix_split_bill_settlements_debt_id'), 'split_bill_settlements', ['debt_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_split_bill_settlements_debt_id'), table_name='split_bill_settlements')
    op.drop_index(op.f('ix_split_bill_settlements_bill_id'), table_name='split_bill_settlements')
    op.drop_index(op.f('ix_split_bill_settlements_id'), table_name='split_bill_settlements')
    op.drop_table('split_bill_settlements')

    op.drop_index('ix_split_bill_debts_bill_debtor', table_name='split_bill_debts')
    op.drop_index(op.f('ix_split_bill_debts_bill_id'), table_name='split_bill_debts')
    op.drop_index(op.f('ix_split_bill_debts_id'), table_name='split_bill_debts')
    op.drop_table('split_bill_debts')

    op.drop_index(op.f('ix_split_bill_participants_bill_id'), table_name='split_bill_participants')
    op.drop_index(op.f('ix_split_bill_participants_id'), table_name='split_bill_participants')
    op.drop_table('split_bill_participants')

    op.drop_index(op.f('ix_split_bill_items_bill_id'), table_name='split_bill_items')
    op.drop_index(op.f('ix_split_bill_items_id'), table_name='split_bill_items')
    op.drop_table('split_bill_items')

    op.drop_index(op.f('ix_split_bill_charges_bill_id'), table_name='split_bill_charges')
    op.drop_index(op.f('ix_split_bill_charges_id'), table_name='split_bill_charges')
    op.drop_table('split_bill_charges')

    op.drop_index('ix_split_bills_user_active', table_name='split_bills')
    op.drop_index(op.f('ix_split_bills_id'), table_name='split_bills')
    op.drop_table('split_bills')