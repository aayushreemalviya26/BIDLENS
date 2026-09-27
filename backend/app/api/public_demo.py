"""Public judge access for the seeded BidLens sample workspace.

The judge workspace is intentionally interactive for the seeded sample only.
Fresh uploads remain an authenticated officer workflow so a public link cannot
be used as an unrestricted file-processing service.
"""
import os

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import Bidder, ComplianceCheck, Evidence, Requirement, Tender
from app.services.judge_demo import DEMO_ID
from .auth import require_session


def enabled():
    return os.getenv("APP_ENV") == "production" and os.getenv(
        "PUBLIC_JUDGE_DEMO", os.getenv("SEED_JUDGE_DEMO", "false")
    ) == "true"


def require_workspace_access(request: Request, db: Session = Depends(get_db)):
    if not enabled():
        return require_session(request, db)

    route = request.scope["route"].path
    tender = db.query(Tender).filter_by(external_bid_id=DEMO_ID).one_or_none()

    # Discovery endpoints needed before the sample tender is selected.
    if request.method == "GET" and route in {"/api/demo/workspace", "/api/tenders"}:
        return None
    if tender is None:
        raise HTTPException(404, "Sample workspace is not available yet")

    params = request.path_params
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

    # Job polling/start targets are checked separately because their path
    # parameter is generic.
    if route == "/api/jobs/{kind}/{target_id}":
        kind = params.get("kind")
        target_id = params.get("target_id")
        if kind == "tender":
            target_tender = int(target_id)
        elif kind == "bidder":
            bidder = db.get(Bidder, target_id)
            target_tender = bidder.tender_id if bidder else None

    allowed_get = {
        "/api/tenders/{tender_id}", "/api/tenders/{tender_id}/requirements",
        "/api/tenders/{tender_id}/bidders", "/api/tenders/{tender_id}/documents/original/file",
        "/api/tenders/{tender_id}/compliance-matrix", "/api/tenders/{tender_id}/document-completeness",
        "/api/tenders/{tender_id}/audit", "/api/bidders/{bidder_db_id}/report",
        "/api/bidders/{bidder_db_id}/documents/{uploaded_file_id}/file",
        "/api/compliance/{check_id}/evidence", "/api/requirements/{requirement_id}/source",
        "/api/evidence/{evidence_id}/source", "/api/jobs/{job_id}",
    }
    allowed_post = {
        # Safe judge interactions on the seeded sample. These do not create
        # arbitrary public uploads or new tender/bidder records.
        "/api/tenders/{tender_id}/evaluate",
        "/api/compliance/{check_id}/accept",
        "/api/compliance/{check_id}/clarification",
        "/api/compliance/{check_id}/override",
    }

    if request.method == "GET" and route in allowed_get:
        pass
    elif request.method == "POST" and route in allowed_post:
        pass
    else:
        # Upload/create/extract/process remain available after normal officer
        # sign-in, but are deliberately not anonymous on the public URL.
        return require_session(request, db)

    if target_tender is not None and str(target_tender) != str(tender.id):
        raise HTTPException(404, "Sample resource not found")
    return None
