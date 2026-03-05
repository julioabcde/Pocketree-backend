from app.db.base_class import Base  # noqa: F401

# Import all models here to ensure they are registered with SQLAlchemy's metadata
# This is necessary for Alembic's autogenerate feature to detect schema changes
from app.modules.auth.model import User  # noqa: F401