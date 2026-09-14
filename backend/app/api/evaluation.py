from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import Bidder, BidderDocument, BidderUploadedFile, ClarificationRequest, ComplianceCheck, Evidence, OfficerDecision, RegistryVerification, Requirement, Tender
from app.schemas.compliance import AcceptRequest, ClarificationCreate, OverrideCreate
from app.services.audit_service import AuditService
from app.services.compliance_engine import ComplianceEngine
from app.services.explainability_service import ExplainabilityService
from app.services.registry_service import RegistryService
from app.services.scoring_service import ScoringService
from .common import get_bidder, get_tender, requirement_payload


router = APIRouter(tags=["evaluation"])
audit = AuditService()


def _verification_payload(item):
    return {"source": item.source, "identifier": item.identifier, "status": item.status, "matched": item.matched, "record": item.registry_record_json, "discrepancies": item.discrepancies_json}


def _verification_for(requirement, evidence, verifications):
    fields = " ".join((item.field or "") for item in evidence).upper()
    category = f"{requirement.category} {requirement.required_document_type or ''}".upper()
    return next((item for item in verifications if item.source in fields or item.source in category), None)


@router.post("/tenders/{tender_id}/evaluate")
def evaluate_tender(tender_id: int, db: Session = Depends(get_db)):
    tender = get_tender(db, tender_id)
    requirements = db.query(Requirement).filter_by(tender_id=tender_id).order_by(Requirement.id).all()
    bidders = db.query(Bidder).filter_by(tender_id=tender_id).all()
    if not requirements:
        raise HTTPException(409, "No requirements have been extracted")
    engine, scorer, explainer, registry = ComplianceEngine(), ScoringService(), ExplainabilityService(), RegistryService()
    for bidder in bidders:
        all_evidence = db.query(Evidence).filter_by(bidder_id=bidder.id).all()
        verifications = registry.verify_evidence(db, bidder, all_evidence)
        for verification in verifications:
            audit.record(db, tender_id, "REGISTRY_VERIFIED", "RegistryVerification", verification.id, {"source": verification.source, "status": verification.status})
        checks = []
        for requirement in requirements:
            evidence = [item for item in all_evidence if item.requirement_id == requirement.requirement_id]
            verification = _verification_for(requirement, evidence, verifications)
            verdict = engine.evaluate(requirement, evidence, verification, bidder.bidder_name)
            explanation = explainer.build(requirement, evidence, verification, verdict["status"], verdict["reason"])
            check = db.query(ComplianceCheck).filter_by(bidder_id=bidder.id, requirement_id=requirement.requirement_id).one_or_none()
            if check is None:
                check = ComplianceCheck(bidder_id=bidder.id, requirement_id=requirement.requirement_id)
                db.add(check)
            check.machine_status = verdict["status"]
            has_officer_decision = check.id is not None and db.query(OfficerDecision.id).filter_by(compliance_check_id=check.id).first() is not None
            if not has_officer_decision:
                check.effective_status = verdict["status"]
            check.required = "MANDATORY" if requirement.mandatory else "OPTIONAL"
            check.found = verdict["found"]
            check.rule = requirement.operator
            check.reason = verdict["reason"]
            check.explanation = explanation["explanation"]
            checks.append(check)
            audit.record(db, tender_id, "RULE_EXECUTED", "ComplianceCheck", requirement.requirement_id, {"operator": requirement.operator, "status": verdict["status"]})
        db.flush()
        bidder.compliance_score, bidder.risk_level, bidder.overall_status = scorer.calculate(checks)
        audit.record(db, tender_id, "COMPLIANCE_GENERATED", "Bidder", bidder.id, {"checks": len(checks)})
        audit.record(db, tender_id, "SCORE_CALCULATED", "Bidder", bidder.id, {"score": bidder.compliance_score})
        audit.record(db, tender_id, "RISK_CALCULATED", "Bidder", bidder.id, {"risk": bidder.risk_level})
    tender.status = "EVALUATED"
    db.commit()
    return {"tender_id": tender_id, "bidders_evaluated": len(bidders)}


@router.get("/tenders/{tender_id}/compliance-matrix")
def compliance_matrix(tender_id: int, db: Session = Depends(get_db)):
    tender = get_tender(db, tender_id)
    requirements = db.query(Requirement).filter_by(tender_id=tender_id).order_by(Requirement.id).all()
    bidders = db.query(Bidder).filter_by(tender_id=tender_id).order_by(Bidder.id).all()
    bidder_payloads = []
    for bidder in bidders:
        documents = db.query(BidderDocument).filter_by(bidder_id=bidder.id).all()
        verifications = db.query(RegistryVerification).filter_by(bidder_id=bidder.id).all()
        checks = {item.requirement_id: item for item in db.query(ComplianceCheck).filter_by(bidder_id=bidder.id).all()}
        cells = []
        for requirement in requirements:
            check = checks.get(requirement.requirement_id)
            expected = requirement.required_document_type
            document = next((item for item in documents if expected and item.category == expected), None)
            cells.append({"compliance_id": check.id if check else None, "requirement_id": requirement.requirement_id, "document_id": document.document_id if document else None, "status": check.effective_status if check else ("NOT_APPLICABLE" if not requirement.applicable else "NOT_EVALUATED"), "machine_status": check.machine_status if check else None, "reason": check.reason if check else "Evaluation has not been run.", "rule": check.rule if check else requirement.operator})
        bidder_payloads.append({"id": bidder.id, "bidder_id": bidder.bidder_id, "bidder_name": bidder.bidder_name, "overall_status": bidder.overall_status, "compliance_score": bidder.compliance_score, "risk_level": bidder.risk_level, "identity_masking": "NOT_APPLIED", "cells": cells, "documents": [{"document_id": item.document_id, "category": item.category, "document_title": item.document_title, "original_file_name": item.filename, "page_start": item.page_start, "page_end": item.page_end, "pages": item.pages_json, "confidence": item.confidence, "processing_status": item.processing_status} for item in documents], "registry_verifications": [_verification_payload(item) for item in verifications]})
    document_url = f"/api/tenders/{tender.id}/documents/original/file" if tender.document_path else None
    return {"id": tender.id, "external_bid_id": tender.external_bid_id, "status": tender.status, "title": tender.title, "department": tender.department, "documentUrl": document_url, "requirements": [requirement_payload(item) for item in requirements], "bidders": bidder_payloads}


@router.get("/tenders/{tender_id}/document-completeness")
def document_completeness(tender_id: int, db: Session = Depends(get_db)):
    get_tender(db, tender_id)
    requirements = db.query(Requirement).filter_by(tender_id=tender_id, approved=True).all()
    bidders = db.query(Bidder).filter_by(tender_id=tender_id).all()
    rows = []
    for requirement in requirements:
        for bidder in bidders:
            docs = db.query(BidderDocument).filter_by(bidder_id=bidder.id, category=requirement.required_document_type).all() if requirement.required_document_type else []
            status = "NOT_APPLICABLE" if not requirement.applicable else ("PRESENT" if docs else ("NEEDS_REVIEW" if not requirement.required_document_type else "MISSING"))
            sources = []
            for item in docs:
                uploaded = db.get(BidderUploadedFile, item.uploaded_file_id) if item.uploaded_file_id else None
                page_start = item.page_start - uploaded.page_start + 1 if uploaded and item.page_start else item.page_start
                page_end = item.page_end - uploaded.page_start + 1 if uploaded and item.page_end else item.page_end
                sources.append({"document_id": item.document_id, "document_title": item.document_title or requirement.name, "original_file_name": uploaded.filename if uploaded else item.filename, "page_start": page_start, "page_end": page_end, "file_url": f"/api/bidders/{bidder.id}/documents/{uploaded.id}/file" if uploaded else None})
            rows.append({"requirement_id": requirement.requirement_id, "category": requirement.required_document_type or requirement.category, "bidder_id": bidder.bidder_id, "bidder_db_id": bidder.id, "status": status, "document_ids": [item.document_id for item in docs], "sources": sources})
    return {"tender_id": tender_id, "rows": rows}


@router.get("/bidders/{bidder_db_id}/report")
def bidder_report(bidder_db_id: int, db: Session = Depends(get_db)):
    bidder = get_bidder(db, bidder_db_id)
    checks = db.query(ComplianceCheck).filter_by(bidder_id=bidder.id).all()
    verifications = db.query(RegistryVerification).filter_by(bidder_id=bidder.id).all()
    return {"bidder": {"id": bidder.id, "bidder_id": bidder.bidder_id, "bidder_name": bidder.bidder_name, "overall_status": bidder.overall_status, "compliance_score": bidder.compliance_score, "risk_level": bidder.risk_level}, "checks": [{"id": item.id, "requirement_id": item.requirement_id, "machine_status": item.machine_status, "effective_status": item.effective_status, "rule": item.rule, "reason": item.reason, "explanation": item.explanation} for item in checks], "registry_verifications": [_verification_payload(item) for item in verifications]}


@router.get("/compliance/{check_id}/evidence")
def compliance_evidence(check_id: int, db: Session = Depends(get_db)):
    check = db.get(ComplianceCheck, check_id)
    if not check:
        raise HTTPException(404, "Compliance check not found")
    bidder = get_bidder(db, check.bidder_id)
    requirement = db.query(Requirement).filter_by(tender_id=bidder.tender_id, requirement_id=check.requirement_id).one()
    evidence = db.query(Evidence).filter_by(bidder_id=bidder.id, requirement_id=check.requirement_id).all()
    verifications = db.query(RegistryVerification).filter_by(bidder_id=bidder.id).all()
    verification = _verification_for(requirement, evidence, verifications)
    explanation = ExplainabilityService().build(requirement, evidence, verification, check.effective_status, check.explanation)
    tender = get_tender(db, bidder.tender_id)
    documents = {item.document_id: item for item in db.query(BidderDocument).filter_by(bidder_id=bidder.id).all()}
    uploaded = db.query(BidderUploadedFile).filter_by(bidder_id=bidder.id).all()
    evidence_payload = []
    for item in evidence:
        document = documents.get(item.document_id)
        source = next((entry for entry in uploaded if document and entry.id == document.uploaded_file_id), None)
        if source is None:
            source = next((entry for entry in uploaded if item.page and entry.page_start <= item.page <= entry.page_end), None)
        page_start = document.page_start - source.page_start + 1 if document and source and document.page_start else None
        page_end = document.page_end - source.page_start + 1 if document and source and document.page_end else None
        evidence_payload.append({"document_id": item.document_id, "document_title": document.document_title if document else requirement.name, "document_category": document.category if document else requirement.required_document_type, "page": item.page, "page_start": page_start, "page_end": page_end, "source_page": (item.page - source.page_start + 1) if source and item.page else item.page, "source_filename": source.filename if source else (document.filename if document else None), "source_file_id": source.id if source else None, "source_url": f"/api/bidders/{bidder.id}/documents/{source.id}/file" if source else None, "field": item.field, "value": item.value, "unit": item.unit, "evidence_text": item.evidence_text, "confidence": document.confidence if document else None, "ambiguities": item.ambiguities_json})
    latest_decision = db.query(OfficerDecision).filter_by(compliance_check_id=check.id).order_by(OfficerDecision.timestamp.desc()).first()
    return {"compliance_id": check.id, "tender_id": bidder.tender_id, "tender_document_url": f"/api/tenders/{tender.id}/documents/original/file" if tender.document_path else None, "bidder": {"id": bidder.id, "bidder_id": bidder.bidder_id, "bidder_name": bidder.bidder_name, "identity_masking": "NOT_APPLIED"}, "requirement": requirement_payload(requirement), "machine_status": check.machine_status, "effective_status": check.effective_status, "reason": check.reason, "officer_decision": {"action": latest_decision.action, "reason": latest_decision.remarks, "verified_by": latest_decision.actor, "verified_at": latest_decision.timestamp} if latest_decision else None, **explanation, "evidence": evidence_payload}


def _decide(check_id: int, action: str, new_status: str, remarks: str | None, actor: str, db: Session):
    check = db.get(ComplianceCheck, check_id)
    if not check:
        raise HTTPException(404, "Compliance check not found")
    bidder = get_bidder(db, check.bidder_id)
    requirement = db.query(Requirement).filter_by(tender_id=bidder.tender_id, requirement_id=check.requirement_id).one_or_none()
    evidence = db.query(Evidence).filter_by(bidder_id=bidder.id, requirement_id=check.requirement_id).first()
    document = db.query(BidderDocument).filter_by(bidder_id=bidder.id, document_id=evidence.document_id).one_or_none() if evidence and evidence.document_id else None
    uploaded = db.get(BidderUploadedFile, document.uploaded_file_id) if document and document.uploaded_file_id else None
    old = check.effective_status
    check.effective_status = new_status
    db.add(OfficerDecision(compliance_check_id=check.id, action=action, old_status=old, new_status=new_status, remarks=remarks, actor=actor))
    db.flush()
    bidder.compliance_score, bidder.risk_level, bidder.overall_status = ScoringService().calculate(
        db.query(ComplianceCheck).filter_by(bidder_id=bidder.id).all()
    )
    page_start = document.page_start - uploaded.page_start + 1 if document and uploaded and document.page_start else (evidence.page if evidence else None)
    page_end = document.page_end - uploaded.page_start + 1 if document and uploaded and document.page_end else page_start
    audit.record(db, bidder.tender_id, action, "ComplianceCheck", check.id, {"requirement": requirement.name if requirement else check.requirement_id, "requirement_id": check.requirement_id, "bidder": bidder.bidder_name, "bidder_id": bidder.bidder_id, "document": document.document_title if document else None, "original_file": uploaded.filename if uploaded else (document.filename if document else None), "page_start": page_start, "page_end": page_end, "machine_status": check.machine_status, "officer_status": new_status, "reason": remarks}, actor=actor)
    db.commit()
    return {"id": check.id, "machine_status": check.machine_status, "effective_status": check.effective_status}


@router.post("/compliance/{check_id}/accept")
def accept_finding(check_id: int, payload: AcceptRequest, db: Session = Depends(get_db)):
    check = db.get(ComplianceCheck, check_id)
    if not check:
        raise HTTPException(404, "Compliance check not found")
    return _decide(check_id, "FINDING_ACCEPTED", check.machine_status, payload.remarks, payload.actor, db)


@router.post("/compliance/{check_id}/clarification")
def request_clarification(check_id: int, payload: ClarificationCreate, db: Session = Depends(get_db)):
    check = db.get(ComplianceCheck, check_id)
    if not check:
        raise HTTPException(404, "Compliance check not found")
    db.add(ClarificationRequest(compliance_check_id=check.id, message=payload.message))
    return _decide(check_id, "CLARIFICATION_REQUESTED", "NEEDS_REVIEW", payload.message, payload.actor, db)


@router.post("/compliance/{check_id}/override")
def override_finding(check_id: int, payload: OverrideCreate, db: Session = Depends(get_db)):
    return _decide(check_id, "OVERRIDE_PERFORMED", payload.new_status, payload.remarks, payload.actor, db)
