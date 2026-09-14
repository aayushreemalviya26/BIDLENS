from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import AuditEvent
from .common import get_tender


router = APIRouter(tags=["audit"])


@router.get("/tenders/{tender_id}/audit")
def tender_audit(tender_id: int, db: Session = Depends(get_db)):
    get_tender(db, tender_id)
    events = db.query(AuditEvent).filter_by(tender_id=tender_id).order_by(AuditEvent.timestamp.desc()).all()
    return [{"id": item.id, "actor": item.actor, "action": item.action, "entity_type": item.entity_type, "entity_id": item.entity_id, "details": item.details, "timestamp": item.timestamp} for item in events]
