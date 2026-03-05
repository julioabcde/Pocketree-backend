from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import models here so Alembic can detect them
from app.modules.auth.model import User
