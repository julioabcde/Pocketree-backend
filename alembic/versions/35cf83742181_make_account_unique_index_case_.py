from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = '35cf83742181'
down_revision: Union[str, Sequence[str], None] = '3419bcd10f3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add case-insensitive unique index on active accounts."""
    op.create_index(
        "ix_accounts_unique_active",
        "accounts",
        ["user_id", text("LOWER(name)"), "type"],
        unique=True,
        postgresql_where=text("is_deleted = false"),
    )


def downgrade() -> None:
    """Remove unique index on active accounts."""
    op.drop_index("ix_accounts_unique_active", table_name="accounts")