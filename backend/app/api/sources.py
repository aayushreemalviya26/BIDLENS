from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import BidderUploadedFile, Evidence, Requirement
from app.services.pdf_provenance import locate_evidence
from .common import get_bidder, get_tender

router = APIRouter(tags=["evidence sources"])


@router.get("/requirements/{requirement_id}/source")
def requirement_source(requirement_id: int, db: Session = Depends(get_db)):
    item = db.get(Requirement, requirement_id)
    if not item:
        raise HTTPException(404, "Requirement not found")
    tender = get_tender(db, item.tender_id)
    provenance = locate_evidence(tender.document_path, item.source_page, item.source_text, item.provenance)
    item.provenance = provenance
    db.commit()
    return {**provenance, "source_file_id": tender.id, "source_filename": Path(tender.document_path).name.split("_", 1)[-1] if tender.document_path else None, "source_url": f"/api/tenders/{tender.id}/documents/original/file" if tender.document_path else None}


@router.get("/evidence/{evidence_id}/source")
def bidder_evidence_source(evidence_id: int, db: Session = Depends(get_db)):
    item = db.get(Evidence, evidence_id)
    if not item:
        raise HTTPException(404, "Evidence not found")
    bidder = get_bidder(db, item.bidder_id)
    # Evidence page is in the assembled pack. Always select its actual original.
    source = db.query(BidderUploadedFile).filter(BidderUploadedFile.bidder_id == bidder.id, BidderUploadedFile.page_start <= (item.page or 0), BidderUploadedFile.page_end >= (item.page or 0)).first()
    page = item.page - source.page_start + 1 if source and item.page else None
    provenance = locate_evidence(source.stored_path if source else None, page, item.evidence_text, item.provenance)
    item.provenance = provenance
    db.commit()
    return {**provenance, "source_file_id": source.id if source else None, "source_filename": source.filename if source else None, "source_url": f"/api/bidders/{bidder.id}/documents/{source.id}/file" if source else None}
