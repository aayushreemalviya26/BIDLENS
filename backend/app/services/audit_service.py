from sqlalchemy.orm import Session

from app.models import AuditEvent


class AuditService:
    def record(self, db: Session, tender_id: int, action: str, entity_type: str, entity_id=None, details=None, actor="system") -> AuditEvent:
        event = AuditEvent(tender_id=tender_id, actor=actor, action=action, entity_type=entity_type, entity_id=str(entity_id) if entity_id is not None else None, details=details or {})
        db.add(event)
        return event
