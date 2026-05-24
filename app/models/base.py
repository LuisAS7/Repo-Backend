from sqlalchemy.orm import DeclarativeBase, declared_attr
from datetime import datetime

class Base(DeclarativeBase):
    # Define common columns for all tables
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()