import uuid
from datetime import datetime
from typing import Annotated

from sqlalchemy import String, DateTime, text, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

# Define a naming convention for indexes and constraints to ensure consistent naming across the database
POSTGRES_INDEXES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata_obj = MetaData(naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION)

# Define common column types for convenience
uuid_pk = Annotated[
    uuid.UUID, 
    mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
]
created_at_dt = Annotated[
    datetime, 
    mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
]
updated_at_dt = Annotated[
    datetime, 
    mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
]

# Common column types for convenience
str_100 = Annotated[str, mapped_column(String(100))]
str_255 = Annotated[str, mapped_column(String(255))]

# BASE AND MIXINS
class Base(DeclarativeBase):
    metadata = metadata_obj

# Mixin to add created_at and updated_at timestamps to models
class TimestampMixin:
    created_at: Mapped[created_at_dt]
    updated_at: Mapped[updated_at_dt]