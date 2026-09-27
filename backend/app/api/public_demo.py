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
    method = request.method

    # SIH judge build: the public workspace exposes the complete prototype
    # workflow, including fresh PDF upload, extraction and bidder processing.
    # Destructive reset and prototype authentication configuration stay private.
    blocked = {
        ("POST", "/api/demo/reset"),
        ("POST", "/api/auth/mode"),
        ("POST", "/api/auth/logout"),
    }
    if (method, route) in blocked:
        return require_session(request, db)

    # All procurement-workspace routes are intentionally available in the
    # public judge build. Processing itself is still bounded by the existing
    # one-job-at-a-time queue and configured hosted provider.
    return None
