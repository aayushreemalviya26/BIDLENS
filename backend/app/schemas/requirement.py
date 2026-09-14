from pydantic import BaseModel, ConfigDict, Field


class RequirementPatch(BaseModel):
    name: str | None = None
    category: str | None = None
    description: str | None = None
    operator: str | None = None
    required_value: float | None = None
    unit: str | None = None
    mandatory: bool | None = None
    required_document_type: str | None = None
    source_page: int | None = None
    source_clause: str | None = None
    source_text: str | None = None
    applicable: bool | None = None
    approved: bool | None = None
    rule_metadata: dict | None = None


class RequirementCreate(BaseModel):
    name: str
    category: str
    description: str
    operator: str = "EXISTS"
    required_value: float | None = None
    unit: str | None = None
    mandatory: bool = True
    required_document_type: str | None = None
    source_page: int | None = None
    source_clause: str | None = None
    source_text: str | None = None
    applicable: bool = True
    rule_metadata: dict = Field(default_factory=dict)


class RequirementRead(RequirementPatch):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tender_id: int
    requirement_id: str
