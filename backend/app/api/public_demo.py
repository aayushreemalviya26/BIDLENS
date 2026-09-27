"""Deployment-only public READ access, restricted to the seeded judge workspace."""
import os

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import Bidder, ComplianceCheck, Evidence, Requirement, Tender
from app.services.judge_demo import DEMO_ID
from .auth import require_session


def enabled():
    # The judge Blueprint already opts into SEED_JUDGE_DEMO. An explicit false
    # restores authentication without changing code in real deployments.
    return os.getenv("APP_ENV") == "production" and os.getenv("PUBLIC_JUDGE_DEMO", os.getenv("SEED_JUDGE_DEMO", "false")) == "true"


def require_workspace_access(request: Request, db: Session = Depends(get_db)):
    if not enabled():
        return require_session(request, db)
    if request.method != "GET":
        raise HTTPException(403, "Public judge demo is read-only. Changes and AI processing are disabled.")
    route = request.scope["route"].path
    if route in {"/api/demo/workspace", "/api/tenders"}:
        return None
    tender = db.query(Tender).filter_by(external_bid_id=DEMO_ID).one_or_none()
    if tender is None:
        raise HTTPException(404, "Preprocessed demo is not available yet")
    params = request.path_params
    allowed = {
        "/api/tenders/{tender_id}", "/api/tenders/{tender_id}/requirements",
        "/api/tenders/{tender_id}/bidders", "/api/tenders/{tender_id}/documents/original/file",
        "/api/tenders/{tender_id}/compliance-matrix", "/api/tenders/{tender_id}/document-completeness",
        "/api/tenders/{tender_id}/audit", "/api/bidders/{bidder_db_id}/report",
        "/api/bidders/{bidder_db_id}/documents/{uploaded_file_id}/file",
        "/api/compliance/{check_id}/evidence", "/api/requirements/{requirement_id}/source",
        "/api/evidence/{evidence_id}/source",
    }
    if route not in allowed:
        return require_session(request, db)
    target_tender = params.get("tender_id")
    if "bidder_db_id" in params:
        bidder = db.get(Bidder, params["bidder_db_id"])
        target_tender = bidder.tender_id if bidder else None
    for key, model in (("check_id", ComplianceCheck), ("evidence_id", Evidence)):
        if key in params:
            item = db.get(model, params[key])
            bidder = db.get(Bidder, item.bidder_id) if item else None
            target_tender = bidder.tender_id if bidder else None
    if "requirement_id" in params:
        item = db.get(Requirement, params["requirement_id"])
        target_tender = item.tender_id if item else None
    if target_tender is None or str(target_tender) != str(tender.id):
        raise HTTPException(404, "Demo resource not found")
    return None
