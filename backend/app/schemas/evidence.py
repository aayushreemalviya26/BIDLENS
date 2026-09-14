from pydantic import BaseModel


class EvidenceRead(BaseModel):
    requirement_id: str
    document_id: str | None = None
    page: int | None = None
    field: str | None = None
    value: str | None = None
    unit: str | None = None
    evidence_text: str | None = None
    evidence_found: bool
    ambiguities: list[str] = []
