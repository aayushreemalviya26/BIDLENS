from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Bidder, Requirement, Tender


def get_tender(db: Session, tender_id: int) -> Tender:
    tender = db.get(Tender, tender_id)
    if not tender:
        raise HTTPException(404, "Tender not found")
    return tender


def get_bidder(db: Session, bidder_id: int) -> Bidder:
    bidder = db.get(Bidder, bidder_id)
    if not bidder:
        raise HTTPException(404, "Bidder not found")
    return bidder


def requirement_payload(item: Requirement) -> dict:
    return {"id": item.id, "requirement_id": item.requirement_id, "name": item.name, "category": item.category, "description": item.description, "operator": item.operator, "required_value": item.required_value, "unit": item.unit, "mandatory": item.mandatory, "required_document_type": item.required_document_type, "source": {"clause": item.source_clause, "page": item.source_page, "text": item.source_text}, "applicable": item.applicable, "approved": item.approved, "metadata": item.rule_metadata or {}}
