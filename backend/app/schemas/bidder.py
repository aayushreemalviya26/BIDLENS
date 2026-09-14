from pydantic import BaseModel, ConfigDict


class BidderCreate(BaseModel):
    bidder_id: str
    bidder_name: str


class BidderRead(BidderCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tender_id: int
    overall_status: str
    compliance_score: float | None = None
    risk_level: str | None = None
