from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
    )


# GLOBAL REUSABLE TYPES
NameStr = Annotated[str, Field(min_length=2, max_length=100)]
PhoneStr = Annotated[str, Field(pattern=r"^\+?[0-9\s\-]{7,20}$")]
ClinicalNoteStr = Annotated[str, Field(max_length=5000)]
ShortReasonStr = Annotated[str, Field(max_length=500)]
