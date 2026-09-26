"""Build a reviewed, portable demo fixture. Never exports sessions or databases.

Bharat is the saved live Ollama acceptance result. Additional synthetic packs
are explicitly curated from literal PDF fields, not claimed as fresh AI output.
"""
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tmp/local-preview/bidlens.db"
TARGET = ROOT / "backend/demo_assets/workspace.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    connection = sqlite3.connect(f"file:{SOURCE.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    def rows(table):
        data = [dict(row) for row in connection.execute(f'SELECT * FROM "{table}"')]
        for row in data:
            for key in ("rule_metadata", "provenance", "pages_json", "ambiguities_json", "registry_record_json", "discrepancies_json", "details"):
                if key in row and isinstance(row[key], str):
                    row[key] = json.loads(row[key])
        return data
    tables = {name: rows(name) for name in ("tenders", "requirements", "bidders", "bidder_uploaded_files", "bidder_documents", "evidence", "compliance_checks", "registry_verifications", "officer_decisions", "clarification_requests")}
    assert len(tables["tenders"]) == 1 and len(tables["bidders"]) == 1
    documents = {}
    tender = tables["tenders"][0]
    assert tender["external_bid_id"] == "GEM/2026/B/7910945"
    real = ROOT / "demo_files/tender/GEM_2026_B_7910945.pdf"
    assert digest(Path(tender["document_path"])) == digest(real)
    tender["document_path"] = real.relative_to(ROOT).as_posix()
    tender["title"] = "Preprocessed Demo — GeM desktop procurement"
    tender["department"] = "SIH judge demonstration / simulated registries"
    documents[tender["document_path"]] = digest(real)
    for bidder in tables["bidders"]:
        bidder["source_file"] = None
    for document in tables["bidder_documents"]:
        document["filename"] = Path(document["filename"]).name if document["filename"] else None
    for row in tables["bidder_uploaded_files"]:
        path = ROOT / "demo_files/bidders/bharat_compute" / row["filename"]
        assert digest(path) == digest(Path(row["stored_path"]))
        text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
        assert "SYNTHETIC DOCUMENT" in text and "fictional" in text
        row["stored_path"] = path.relative_to(ROOT).as_posix()
        documents[row["stored_path"]] = digest(path)
    # Preserve actual historical provider timestamps without paths/errors/session data.
    tables["audit_events"] = [row for row in rows("audit_events") if row["action"] in {"TENDER_EXTRACTION_COMPLETED", "BIDDER_PROCESSING_COMPLETED", "REQUIREMENTS_APPROVED"}]
    for row in tables["audit_events"]:
        row["details"]["preprocessed"] = True
    # Two additional curated synthetic examples use the same generic PDF field
    # reader. They are not sent through the live AI pipeline during deployment.
    next_id = lambda name: max((row["id"] for row in tables[name]), default=0) + 1
    template = {row["filename"]: row for row in tables["bidder_documents"]}
    field_map = {
        "Udyam_Certificate.pdf": ("Udyam Registration Number", "Udyam Number"),
        "GST_Registration.pdf": ("GSTIN", "GSTIN"),
        "PAN_Card.pdf": ("PAN", "PAN"),
        "Local_Content_Declaration.pdf": ("Percentage of Local Content", "LocalContentPercentage"),
        "OEM_Authorization.pdf": ("Authorized Bidder", "Authorized Bidder"),
        "BIS_Technical_Compliance.pdf": ("BIS Licence Number", "BIS Licence Number"),
        "Bidder_Turnover_Certificate.pdf": ("Average Annual Turnover", "Average Annual Turnover"),
        "OEM_Turnover_Certificate.pdf": ("Average Annual Turnover", "OEM Average Annual Turnover"),
    }
    def field(text, name):
        match = re.search(r"(?:^|\n)" + re.escape(name) + r"\s*\n([^\n]+)", text)
        if not match:
            raise ValueError(f"Curated PDF field not found: {name}")
        return match.group(1).strip()
    for folder in ("orange_tech", "securebyte"):
        pack = ROOT / "demo_files/bidders" / folder
        company = PdfReader(pack / "Company_Profile.pdf").pages[0].extract_text()
        bidder_id = next_id("bidders")
        tables["bidders"].append({"id": bidder_id, "tender_id": tender["id"], "bidder_id": field(company, "Bidder ID"), "bidder_name": field(company, "Registered Bidder"), "source_file": None, "overall_status": "NOT_EVALUATED", "compliance_score": None, "risk_level": None})
        page_start = 1
        for path in sorted(pack.glob("*.pdf")):
            reader = PdfReader(path)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            assert "SYNTHETIC DOCUMENT" in text and "fictional" in text
            relative = path.relative_to(ROOT).as_posix()
            documents[relative] = digest(path)
            upload_id = next_id("bidder_uploaded_files")
            tables["bidder_uploaded_files"].append({"id": upload_id, "bidder_id": bidder_id, "filename": path.name, "stored_path": relative, "page_start": page_start, "page_end": page_start + len(reader.pages) - 1})
            base = template[path.name]
            document_id = f"CURATED-{bidder_id}-{upload_id}"
            tables["bidder_documents"].append({**base, "id": next_id("bidder_documents"), "bidder_id": bidder_id, "uploaded_file_id": upload_id, "document_id": document_id, "page_start": page_start, "page_end": page_start + len(reader.pages) - 1, "pages_json": list(range(page_start, page_start + len(reader.pages))), "confidence": None, "processing_status": "PREPROCESSED_CURATED"})
            if path.name in field_map:
                label, evidence_field = field_map[path.name]
                value = field(text, label)
                # Match by the existing tested document-to-requirement mapping,
                # never by bidder identity or an expected verdict.
                req_ids = {ev["requirement_id"] for ev in tables["evidence"] if ev["bidder_id"] == 1 and ev["document_id"] == base["document_id"]}
                for req_id in sorted(req_ids):
                    requirement = next(r for r in tables["requirements"] if r["requirement_id"] == req_id)
                    # Do not mix OEM and bidder turnover from broad AI retrieval.
                    kind = requirement.get("rule_metadata", {}).get("entity", "")
                    description = (requirement["name"] + " " + requirement["description"]).lower()
                    if "Turnover" in path.name and (("oem" in description) != (path.name.startswith("OEM_"))):
                        continue
                    tables["evidence"].append({"id": next_id("evidence"), "bidder_id": bidder_id, "requirement_id": req_id, "document_id": document_id, "page": page_start, "field": evidence_field, "value": value, "unit": "PERCENT" if "%" in value else ("INR" if value.startswith("INR") else None), "evidence_text": label + "\n" + value, "evidence_found": True, "ambiguities_json": [], "provenance": None})
            page_start += len(reader.pages)
    fixture = {"version": 1, "label": "Preprocessed Demo", "origin": "Bharat: saved local Ollama live acceptance. Orange/SecureByte: curated literal PDF fields, not AI-generated. All findings are recomputed by the unchanged compliance engine at seed time.", "documents": documents, "tables": tables}
    encoded = json.dumps(fixture, indent=2, ensure_ascii=False, default=str)
    forbidden = re.search(r"[A-Za-z]:\\\\|/Users/|token_hash|API_KEY|password", encoded, re.I)
    assert not forbidden, encoded[max(0, forbidden.start() - 70):forbidden.start() + 120] if forbidden else ""
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(encoded, encoding="utf-8")
    print(f"Exported {len(documents)} allowlisted PDFs; 3 synthetic bidders; no sessions or secrets.")


if __name__ == "__main__":
    main()
