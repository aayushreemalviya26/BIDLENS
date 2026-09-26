from pathlib import Path
import os
import shutil

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import AuditEvent, Bidder, BidderDocument, BidderUploadedFile, ClarificationRequest, ComplianceCheck, Evidence, OfficerDecision, RegistryVerification, Requirement, Tender
from app.services.storage_service import StorageService


router = APIRouter(tags=["demo"])


@router.get("/demo/workspace")
def demo_workspace(db: Session = Depends(get_db)):
    from app.services.judge_demo import DEMO_ID
    tender = db.query(Tender).filter_by(external_bid_id=DEMO_ID).one_or_none()
    return {"tender_id": tender.id if tender else None, "label": "Preprocessed Demo", "hosted": os.getenv("APP_ENV") == "production", "limitations": "Saved demonstration, not fresh AI. Registries are simulated. Fresh uploads are temporary on the free host."}


@router.post("/demo/reset")
def reset_demo(db: Session = Depends(get_db)):
    if os.getenv("APP_ENV") == "production":
        raise HTTPException(403, "Reset is disabled on the shared judge demo. Start a new evaluation instead.")
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
