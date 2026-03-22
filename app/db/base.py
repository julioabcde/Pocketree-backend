from app.db.base_class import Base  # noqa: F401

# Import all models here to ensure they are registered with SQLAlchemy's metadata
# This is necessary for Alembic's autogenerate feature to detect schema changes
from app.modules.auth.models import User  # noqa: F401
from app.modules.accounts.models import Account  # noqa: F401
from app.modules.category.models import Category  # noqa: F401
from app.modules.transactions.models import Transaction  # noqa: F401