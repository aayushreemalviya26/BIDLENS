from typing import Literal

from pydantic import BaseModel, Field


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
