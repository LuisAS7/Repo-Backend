from typing import Any
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import declared_attr

class Base(DeclarativeBase):
    id: Any
    __name__: str
    
    # Genera automáticamente el nombre de la tabla en minúsculas si no se define
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()