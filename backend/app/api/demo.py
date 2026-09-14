from pathlib import Path
import shutil

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import AuditEvent, Bidder, BidderDocument, BidderUploadedFile, ClarificationRequest, ComplianceCheck, Evidence, OfficerDecision, RegistryVerification, Requirement, Tender
from app.services.storage_service import StorageService


router = APIRouter(tags=["demo"])


@router.post("/demo/reset")
def reset_demo(db: Session = Depends(get_db)):
    for model in (ClarificationRequest, OfficerDecision, ComplianceCheck, RegistryVerification, Evidence, BidderDocument, BidderUploadedFile, AuditEvent, Requirement, Bidder, Tender):
        db.query(model).delete()
    db.commit()
    upload_root = StorageService().root.resolve()
    for child in upload_root.iterdir():
        resolved = child.resolve()
        if resolved.parent != upload_root or child.name == ".gitkeep":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    return {"status": "RESET", "message": "Demo database and uploaded file references were cleared."}
