from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pypdf import PdfReader, PdfWriter
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import Bidder, BidderDocument, BidderUploadedFile, ComplianceCheck, Evidence, RegistryVerification, Requirement
from app.schemas.bidder import BidderCreate, BidderRead
from app.services.audit_service import AuditService
from app.services.bidder_ai_adapter import BidderAIAdapter
from app.services.storage_service import StorageService
from .common import get_bidder, get_tender, requirement_payload


router = APIRouter(tags=["bidders"])
audit = AuditService()


@router.post("/tenders/{tender_id}/bidders", response_model=BidderRead, status_code=201)
def create_bidder(tender_id: int, payload: BidderCreate, db: Session = Depends(get_db)):
    get_tender(db, tender_id)
    bidder = Bidder(tender_id=tender_id, **payload.model_dump())
    db.add(bidder)
    db.flush()
    audit.record(db, tender_id, "BIDDER_CREATED", "Bidder", bidder.id, {"bidder_id": bidder.bidder_id})
    db.commit()
    db.refresh(bidder)
    return bidder


def _bidder_payload(db: Session, bidder: Bidder) -> dict:
    files = db.query(BidderUploadedFile).filter_by(bidder_id=bidder.id).order_by(BidderUploadedFile.page_start).all()
    documents = db.query(BidderDocument).filter_by(bidder_id=bidder.id).order_by(BidderDocument.page_start).all()
    return {
        "id": bidder.id,
        "tender_id": bidder.tender_id,
        "bidder_id": bidder.bidder_id,
        "bidder_name": bidder.bidder_name,
        "source_file": Path(bidder.source_file).name if bidder.source_file else None,
        "overall_status": bidder.overall_status,
        "compliance_score": bidder.compliance_score,
        "risk_level": bidder.risk_level,
        "uploaded_files": [{"id": item.id, "filename": item.filename, "page_start": 1, "page_end": item.page_end - item.page_start + 1, "url": f"/api/bidders/{bidder.id}/documents/{item.id}/file"} for item in files],
        "documents": [{"document_id": item.document_id, "uploaded_file_id": item.uploaded_file_id, "category": item.category, "document_title": item.document_title, "original_file_name": item.filename, "page_start": item.page_start - source.page_start + 1 if (source := next((entry for entry in files if entry.id == item.uploaded_file_id), None)) and item.page_start else item.page_start, "page_end": item.page_end - source.page_start + 1 if source and item.page_end else item.page_end, "pages": [page - source.page_start + 1 for page in item.pages_json] if source else item.pages_json, "file_url": f"/api/bidders/{bidder.id}/documents/{source.id}/file" if source else None, "confidence": item.confidence, "processing_status": item.processing_status} for item in documents],
    }


@router.get("/tenders/{tender_id}/bidders")
def list_bidders(tender_id: int, db: Session = Depends(get_db)):
    get_tender(db, tender_id)
    return [_bidder_payload(db, item) for item in db.query(Bidder).filter_by(tender_id=tender_id).order_by(Bidder.id).all()]


@router.get("/bidders/{bidder_db_id}/documents/{uploaded_file_id}/file")
def bidder_document_file(bidder_db_id: int, uploaded_file_id: int, db: Session = Depends(get_db)):
    bidder = get_bidder(db, bidder_db_id)
    uploaded = db.query(BidderUploadedFile).filter_by(id=uploaded_file_id, bidder_id=bidder.id).one_or_none()
    if not uploaded:
        raise HTTPException(404, "Bidder document not found")
    path = Path(uploaded.stored_path)
    if not path.is_file():
        raise HTTPException(404, "Bidder document is unavailable")
    return FileResponse(path, media_type="application/pdf", filename=uploaded.filename, content_disposition_type="inline")


@router.post("/bidders/{bidder_db_id}/upload")
def upload_bidder(bidder_db_id: int, files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    bidder = get_bidder(db, bidder_db_id)
    if not files:
        raise HTTPException(400, "Select at least one PDF")
    storage = StorageService()
    try:
        for upload in files:
            path = storage.save_named(upload, f"bidders/{bidder.id}/originals")
            existing = db.query(BidderUploadedFile).filter_by(bidder_id=bidder.id, filename=Path(upload.filename or "").name).one_or_none()
            if existing is None:
                existing = BidderUploadedFile(bidder_id=bidder.id, filename=Path(upload.filename or "").name, stored_path=str(path), page_start=1, page_end=1)
                db.add(existing)
            else:
                existing.stored_path = str(path)
            audit.record(db, bidder.tender_id, "BIDDER_DOCUMENT_UPLOADED", "Bidder", bidder.id, {"filename": upload.filename})
        db.flush()
        uploaded = db.query(BidderUploadedFile).filter_by(bidder_id=bidder.id).order_by(BidderUploadedFile.filename).all()
        combined_path = storage.root / f"bidders/{bidder.id}/bidder_pack.pdf"
        combined_path.parent.mkdir(parents=True, exist_ok=True)
        writer = PdfWriter()
        current_page = 1
        for uploaded_file in uploaded:
            reader = PdfReader(uploaded_file.stored_path)
            uploaded_file.page_start = current_page
            for page in reader.pages:
                writer.add_page(page)
            current_page += len(reader.pages)
            uploaded_file.page_end = current_page - 1
        with combined_path.open("wb") as destination:
            writer.write(destination)
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    except Exception as error:
        raise HTTPException(400, f"Could not assemble bidder PDF pack: {error}") from error
    db.query(ComplianceCheck).filter_by(bidder_id=bidder.id).delete()
    db.query(RegistryVerification).filter_by(bidder_id=bidder.id).delete()
    db.query(Evidence).filter_by(bidder_id=bidder.id).delete()
    db.query(BidderDocument).filter_by(bidder_id=bidder.id).delete()
    bidder.source_file = str(combined_path)
    bidder.overall_status = "NOT_EVALUATED"
    bidder.compliance_score = None
    bidder.risk_level = None
    db.commit()
    return _bidder_payload(db, bidder)


@router.post("/bidders/{bidder_db_id}/process")
def process_bidder(bidder_db_id: int, db: Session = Depends(get_db)):
    bidder = get_bidder(db, bidder_db_id)
    if not bidder.source_file:
        raise HTTPException(409, "Upload a bidder PDF before processing")
    requirements = db.query(Requirement).filter_by(tender_id=bidder.tender_id, approved=True).order_by(Requirement.id).all()
    if not requirements:
        raise HTTPException(409, "Approve tender requirements before processing bidders")
    audit.record(db, bidder.tender_id, "BIDDER_PROCESSING_STARTED", "Bidder", bidder.id)
    db.commit()
    try:
        adapter = BidderAIAdapter()
        adapter.bidder_id, adapter.bidder_name = bidder.bidder_id, bidder.bidder_name
        output = adapter.run(bidder.source_file, [requirement_payload(item) for item in requirements])
    except Exception as error:
        message = str(error)
        if "11434" in message or "ollama" in message.casefold():
            detail = f"Ollama is unavailable or qwen2.5:3b could not run: {message}"
        elif "sentence" in message.casefold() or "embedding" in message.casefold() or "transformer" in message.casefold():
            detail = f"Embedding model all-MiniLM-L6-v2 could not load: {message}"
        else:
            detail = f"Bidder AI pipeline failed: {message}"
        audit.record(db, bidder.tender_id, "BIDDER_PROCESSING_FAILED", "Bidder", bidder.id, {"error": detail})
        db.commit()
        raise HTTPException(502, detail) from error
    db.query(Evidence).filter_by(bidder_id=bidder.id).delete()
    db.query(BidderDocument).filter_by(bidder_id=bidder.id).delete()
    uploaded_files = db.query(BidderUploadedFile).filter_by(bidder_id=bidder.id).all()
    for item in output["documents"]:
        page = item.get("page_start")
        source = next((uploaded for uploaded in uploaded_files if page and uploaded.page_start <= page <= uploaded.page_end), None)
        db.add(BidderDocument(bidder_id=bidder.id, uploaded_file_id=source.id if source else None, document_id=item["document_id"], category=item.get("category", "UNKNOWN"), filename=source.filename if source else Path(bidder.source_file).name, document_title=item.get("document_title"), page_start=item.get("page_start"), page_end=item.get("page_end"), pages_json=item.get("pages") or [], confidence=item.get("confidence"), processing_status="NEEDS_REVIEW" if item.get("needs_review") else "CLASSIFIED"))
        audit.record(db, bidder.tender_id, "DOCUMENT_CLASSIFIED", "BidderDocument", item["document_id"], {"category": item.get("category"), "confidence": item.get("confidence"), "original_file": source.filename if source else None, "page_start": item.get("page_start") - source.page_start + 1 if source and item.get("page_start") else item.get("page_start"), "page_end": item.get("page_end") - source.page_start + 1 if source and item.get("page_end") else item.get("page_end"), "identity_masking": "NOT_APPLIED"})
    for item in output["evidence"]:
        db.add(Evidence(bidder_id=bidder.id, requirement_id=item["requirement_id"], document_id=item.get("document_id"), page=item.get("page"), field=item.get("field"), value=item.get("value"), unit=item.get("unit"), evidence_text=item.get("evidence_text"), evidence_found=item.get("evidence_found", False), ambiguities_json=item.get("ambiguities") or []))
        audit.record(db, bidder.tender_id, "EVIDENCE_EXTRACTED", "Evidence", item["requirement_id"], {"evidence_found": item.get("evidence_found", False)})
    audit.record(db, bidder.tender_id, "BIDDER_PROCESSING_COMPLETED", "Bidder", bidder.id, {"documents": len(output["documents"]), "evidence": len(output["evidence"])})
    db.commit()
    return {"documents": len(output["documents"]), "evidence": len(output["evidence"]), "bidder": _bidder_payload(db, bidder)}
