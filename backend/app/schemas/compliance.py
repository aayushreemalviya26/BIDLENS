from typing import Literal

from pydantic import BaseModel, Field
from pydantic import field_validator


class AcceptRequest(BaseModel):
    remarks: str | None = None
    actor: str = "officer"


class ClarificationCreate(BaseModel):
    message: str = Field(min_length=1)
    actor: str = "officer"


class OverrideCreate(BaseModel):
    new_status: Literal["COMPLIANT", "NON_COMPLIANT", "NEEDS_REVIEW", "NOT_APPLICABLE", "NOT_EVALUATED"]
    remarks: str = Field(min_length=1)
    actor: str = "officer"

    @field_validator("remarks")
    @classmethod
    def nonblank_reason(cls, value):
        if not value.strip():
            raise ValueError("An override reason is required")
        return value.strip()
