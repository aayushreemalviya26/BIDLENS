from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import Requirement, Tender
from app.schemas.requirement import RequirementCreate, RequirementPatch
from app.schemas.tender import TenderCreate, TenderRead
from app.services.audit_service import AuditService
from app.services.storage_service import StorageService
from app.services.tender_ai_adapter import TenderAIAdapter
from .common import get_tender, requirement_payload


router = APIRouter(tags=["tenders"])
audit = AuditService()


def _tender_payload(tender):
    document_url = f"/api/tenders/{tender.id}/documents/original/file" if tender.document_path else None
    return {"id": tender.id, "external_bid_id": tender.external_bid_id, "title": tender.title, "department": tender.department, "status": tender.status, "document_url": document_url, "created_at": tender.created_at}


@router.post("/tenders", response_model=TenderRead, status_code=201)
def create_tender(payload: TenderCreate, db: Session = Depends(get_db)):
    tender = Tender(**payload.model_dump())
    db.add(tender)
    db.flush()
    audit.record(db, tender.id, "TENDER_CREATED", "Tender", tender.id)
    db.commit()
    db.refresh(tender)
    return tender


@router.get("/tenders")
def list_tenders(db: Session = Depends(get_db)):
    return [_tender_payload(item) for item in db.query(Tender).order_by(Tender.created_at.desc()).all()]


@router.get("/tenders/{tender_id}")
def read_tender(tender_id: int, db: Session = Depends(get_db)):
    return _tender_payload(get_tender(db, tender_id))


@router.post("/tenders/{tender_id}/upload")
def upload_tender(tender_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    tender = get_tender(db, tender_id)
    try:
        path = StorageService().save(file, f"tenders/{tender_id}")
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    tender.document_path = str(path)
    tender.status = "UPLOADED"
    audit.record(db, tender.id, "TENDER_UPLOADED", "Tender", tender.id, {"filename": file.filename})
    db.commit()
    return {"id": tender.id, "document_url": f"/api/tenders/{tender.id}/documents/original/file", "status": tender.status}


@router.get("/tenders/{tender_id}/documents/original/file")
def tender_document_file(tender_id: int, db: Session = Depends(get_db)):
    tender = get_tender(db, tender_id)
    if not tender.document_path:
        raise HTTPException(404, "Tender document not found")
    path = Path(tender.document_path)
    if not path.is_file():
        raise HTTPException(404, "Tender document is unavailable")
    return FileResponse(path, media_type="application/pdf", filename=path.name, content_disposition_type="inline")


@router.post("/tenders/{tender_id}/extract")
def extract_tender(tender_id: int, db: Session = Depends(get_db)):
    tender = get_tender(db, tender_id)
    if not tender.document_path:
        raise HTTPException(409, "Upload a tender PDF before extraction")
    audit.record(db, tender.id, "TENDER_EXTRACTION_STARTED", "Tender", tender.id)
    db.commit()
    try:
        adapter = TenderAIAdapter()
        output = adapter.run(tender.document_path)
    except Exception as error:
        message = str(error)
        detail = f"Tender AI pipeline failed: {message}"
        if "11434" in message or "ollama" in message.casefold():
            detail = f"Ollama is unavailable or qwen2.5:3b could not run: {message}"
        elif "sentence" in message.casefold() or "embedding" in message.casefold() or "transformer" in message.casefold():
            detail = f"Embedding model all-MiniLM-L6-v2 could not load: {message}"
        audit.record(db, tender.id, "TENDER_EXTRACTION_FAILED", "Tender", tender.id, {"error": detail})
        db.commit()
        raise HTTPException(502, detail) from error
    db.query(Requirement).filter_by(tender_id=tender.id).delete()
    for item in output:
        source = item.get("source") or {}
        row = Requirement(tender_id=tender.id, requirement_id=item["requirement_id"], name=item["name"], category=item["category"], description=item["description"], operator=item["operator"], required_value=item.get("required_value"), unit=item.get("unit"), mandatory=item.get("mandatory", True), required_document_type=item.get("required_document_type"), source_page=source.get("page"), source_clause=source.get("clause"), source_text=source.get("text"), applicable=item.get("applicable", True), approved=False, rule_metadata=item.get("metadata") or {})
        db.add(row)
        audit.record(db, tender.id, "REQUIREMENT_EXTRACTED", "Requirement", item["requirement_id"], {"applicable": item.get("applicable", True)})
    tender.status = "REVIEW_REQUIRED"
    audit.record(db, tender.id, "TENDER_EXTRACTION_COMPLETED", "Tender", tender.id, adapter.normalizer.stats)
    db.commit()
    return {"count": len(output), "requirements": output}


@router.get("/tenders/{tender_id}/requirements")
def list_requirements(tender_id: int, db: Session = Depends(get_db)):
    get_tender(db, tender_id)
    return [requirement_payload(item) for item in db.query(Requirement).filter_by(tender_id=tender_id).order_by(Requirement.id).all()]


@router.post("/tenders/{tender_id}/requirements", status_code=201)
def create_requirement(tender_id: int, payload: RequirementCreate, db: Session = Depends(get_db)):
    tender = get_tender(db, tender_id)
    latest = db.query(Requirement).filter_by(tender_id=tender_id).order_by(Requirement.id.desc()).first()
    sequence = (latest.id if latest else 0) + 1
    requirement_id = f"REQ{sequence:03d}"
    while db.query(Requirement).filter_by(tender_id=tender_id, requirement_id=requirement_id).first():
        sequence += 1
        requirement_id = f"REQ{sequence:03d}"
    row = Requirement(tender_id=tender_id, requirement_id=requirement_id, approved=False, **payload.model_dump())
    db.add(row)
    db.flush()
    audit.record(db, tender.id, "REQUIREMENT_ADDED", "Requirement", requirement_id, payload.model_dump())
    db.commit()
    db.refresh(row)
    return requirement_payload(row)


@router.patch("/requirements/{requirement_db_id}")
def patch_requirement(requirement_db_id: int, payload: RequirementPatch, db: Session = Depends(get_db)):
    item = db.get(Requirement, requirement_db_id)
    if not item:
        raise HTTPException(404, "Requirement not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    audit.record(db, item.tender_id, "REQUIREMENT_EDITED", "Requirement", item.requirement_id, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(item)
    return requirement_payload(item)


@router.delete("/requirements/{requirement_db_id}")
def delete_requirement(requirement_db_id: int, db: Session = Depends(get_db)):
    item = db.get(Requirement, requirement_db_id)
    if not item:
        raise HTTPException(404, "Requirement not found")
    tender_id, requirement_id = item.tender_id, item.requirement_id
    db.delete(item)
    audit.record(db, tender_id, "REQUIREMENT_DELETED", "Requirement", requirement_id)
    db.commit()
    return {"deleted": requirement_id}


@router.post("/tenders/{tender_id}/approve")
def approve_requirements(tender_id: int, db: Session = Depends(get_db)):
    tender = get_tender(db, tender_id)
    count = db.query(Requirement).filter_by(tender_id=tender_id, applicable=True).update({Requirement.approved: True})
    tender.status = "CHECKLIST_APPROVED"
    audit.record(db, tender.id, "CHECKLIST_APPROVED", "Tender", tender.id, {"approved_requirements": count}, actor="officer")
    db.commit()
    return {"status": tender.status, "approved_requirements": count}
