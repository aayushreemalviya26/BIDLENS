from pydantic import BaseModel, ConfigDict


class TenderCreate(BaseModel):
    external_bid_id: str | None = None
    title: str
    department: str | None = None


class TenderRead(TenderCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    document_url: str | None = None
