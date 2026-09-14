from pathlib import Path
from io import BytesIO

from pypdf import PdfWriter

from app.models import AuditEvent, Bidder, ComplianceCheck, Evidence, Requirement
from app.services.bidder_ai_adapter import BidderAIAdapter
from app.services.storage_service import StorageService


def create_tender(client):
    response = client.post("/api/tenders", json={"external_bid_id": "GEM/TEST/1", "title": "Test Tender", "department": "QA"})
    assert response.status_code == 201
    return response.json()["id"]


def pdf_bytes(page_count=1):
    stream = BytesIO()
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=595, height=842)
    writer.write(stream)
    return stream.getvalue()


def approved_requirement(db, tender_id, requirement_id, category):
    row = Requirement(tender_id=tender_id, requirement_id=requirement_id, name=category, category=category, description=category, operator="EXISTS", mandatory=True, required_document_type=category, applicable=True, approved=True, rule_metadata={})
    db.add(row)
    db.commit()
    return row


def test_tender_upload_and_audit_persistence(client, db, monkeypatch, tmp_path):
    tender_id = create_tender(client)
    target = tmp_path / "tender.pdf"
    monkeypatch.setattr(StorageService, "save", lambda self, upload, namespace: target)
    response = client.post(f"/api/tenders/{tender_id}/upload", files={"file": ("tender.pdf", b"%PDF-1.4", "application/pdf")})
    assert response.status_code == 200
    actions = [event.action for event in db.query(AuditEvent).filter_by(tender_id=tender_id).all()]
    assert {"TENDER_CREATED", "TENDER_UPLOADED"}.issubset(actions)


def test_bidder_process_persists_evidence_and_document_completeness(client, db, monkeypatch, tmp_path):
    tender_id = create_tender(client)
    req = Requirement(tender_id=tender_id, requirement_id="REQ001", name="GST", category="GST", description="GSTIN", operator="EXISTS", mandatory=True, required_document_type="GST", applicable=True, approved=True, rule_metadata={})
    db.add(req); db.commit()
    bidder_response = client.post(f"/api/tenders/{tender_id}/bidders", json={"bidder_id": "B01", "bidder_name": "Bidder One"})
    bidder_id = bidder_response.json()["id"]
    bidder = db.get(Bidder, bidder_id); bidder.source_file = str(tmp_path / "bidder.pdf"); db.commit()
    monkeypatch.setattr(BidderAIAdapter, "run", lambda self, path, requirements: {"documents": [{"document_id": "DOC001", "category": "GST", "page_start": 1, "page_end": 1, "pages": [1], "confidence": .99}], "evidence": [{"requirement_id": "REQ001", "document_id": "DOC001", "page": 1, "field": "GSTIN", "value": "22AAAAA0000A1Z5", "unit": None, "evidence_text": "GSTIN 22AAAAA0000A1Z5", "evidence_found": True, "ambiguities": []}]})
    assert client.post(f"/api/bidders/{bidder_id}/process").status_code == 200
    assert db.query(Evidence).filter_by(bidder_id=bidder_id).count() == 1
    rows = client.get(f"/api/tenders/{tender_id}/document-completeness").json()["rows"]
    assert rows[0]["status"] == "PRESENT"


def test_officer_override_preserves_machine_status_and_is_audited(client, db):
    tender_id = create_tender(client)
    bidder = Bidder(tender_id=tender_id, bidder_id="B01", bidder_name="Bidder", overall_status="FAIL")
    db.add(bidder); db.flush()
    check = ComplianceCheck(bidder_id=bidder.id, requirement_id="REQ001", machine_status="NON_COMPLIANT", effective_status="NON_COMPLIANT", required="MANDATORY", found=None, rule="EXISTS", reason="Missing", explanation="Missing")
    db.add(check); db.commit()
    response = client.post(f"/api/compliance/{check.id}/override", json={"new_status": "COMPLIANT", "remarks": "Verified original", "actor": "qa-officer"})
    assert response.status_code == 200
    db.refresh(check)
    assert check.machine_status == "NON_COMPLIANT"
    assert check.effective_status == "COMPLIANT"
    assert db.query(AuditEvent).filter_by(tender_id=tender_id, action="OVERRIDE_PERFORMED").count() == 1


def test_combined_pdf_traceability_uses_same_original_file(client, db, monkeypatch):
    tender_id = create_tender(client)
    for number, category in enumerate(("GST", "PAN", "UDYAM"), start=1):
        approved_requirement(db, tender_id, f"REQ{number:03d}", category)
    bidder_id = client.post(f"/api/tenders/{tender_id}/bidders", json={"bidder_id": "B02", "bidder_name": "Combined Bidder"}).json()["id"]
    upload = client.post(f"/api/bidders/{bidder_id}/upload", files=[("files", ("ABC_Bid_Documents.pdf", pdf_bytes(22), "application/pdf"))])
    assert upload.status_code == 200
    monkeypatch.setattr(BidderAIAdapter, "run", lambda self, path, requirements: {
        "documents": [
            {"document_id": "GST01", "category": "GST", "document_title": "GST Certificate", "page_start": 18, "page_end": 19, "pages": [18, 19], "confidence": .97},
            {"document_id": "PAN01", "category": "PAN", "document_title": "PAN", "page_start": 20, "page_end": 20, "pages": [20], "confidence": .96},
            {"document_id": "UDY01", "category": "UDYAM", "document_title": "Udyam Certificate", "page_start": 21, "page_end": 22, "pages": [21, 22], "confidence": .95},
        ], "evidence": []})
    result = client.post(f"/api/bidders/{bidder_id}/process")
    assert result.status_code == 200
    documents = result.json()["bidder"]["documents"]
    assert {(item["original_file_name"], item["page_start"], item["page_end"]) for item in documents} == {
        ("ABC_Bid_Documents.pdf", 18, 19), ("ABC_Bid_Documents.pdf", 20, 20), ("ABC_Bid_Documents.pdf", 21, 22)}
    file_id = result.json()["bidder"]["uploaded_files"][0]["id"]
    assert client.get(f"/api/bidders/{bidder_id}/documents/{file_id}/file").headers["content-type"] == "application/pdf"


def test_separate_pdf_traceability_uses_each_original_file(client, db, monkeypatch):
    tender_id = create_tender(client)
    for number, category in enumerate(("GST", "PAN", "UDYAM"), start=1):
        approved_requirement(db, tender_id, f"REQ{number:003d}", category)
    bidder_id = client.post(f"/api/tenders/{tender_id}/bidders", json={"bidder_id": "B03", "bidder_name": "Separate Bidder"}).json()["id"]
    files = [
        ("files", ("GST_Certificate.pdf", pdf_bytes(2), "application/pdf")),
        ("files", ("PAN.pdf", pdf_bytes(1), "application/pdf")),
        ("files", ("Udyam.pdf", pdf_bytes(3), "application/pdf")),
    ]
    assert client.post(f"/api/bidders/{bidder_id}/upload", files=files).status_code == 200
    monkeypatch.setattr(BidderAIAdapter, "run", lambda self, path, requirements: {
        "documents": [
            {"document_id": "GST01", "category": "GST", "document_title": "GST Certificate", "page_start": 1, "page_end": 2, "pages": [1, 2], "confidence": .97},
            {"document_id": "PAN01", "category": "PAN", "document_title": "PAN", "page_start": 3, "page_end": 3, "pages": [3], "confidence": .96},
            {"document_id": "UDY01", "category": "UDYAM", "document_title": "Udyam Certificate", "page_start": 4, "page_end": 6, "pages": [4, 5, 6], "confidence": .95},
        ], "evidence": []})
    result = client.post(f"/api/bidders/{bidder_id}/process")
    assert result.status_code == 200
    documents = {item["category"]: item for item in result.json()["bidder"]["documents"]}
    assert (documents["GST"]["original_file_name"], documents["GST"]["page_start"], documents["GST"]["page_end"]) == ("GST_Certificate.pdf", 1, 2)
    assert (documents["PAN"]["original_file_name"], documents["PAN"]["page_start"], documents["PAN"]["page_end"]) == ("PAN.pdf", 1, 1)
    assert (documents["UDYAM"]["original_file_name"], documents["UDYAM"]["page_start"], documents["UDYAM"]["page_end"]) == ("Udyam.pdf", 1, 3)
