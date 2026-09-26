"""Read-only inspection of the isolated preview's persisted acceptance records."""
import hashlib
import json
from pathlib import Path
import sqlite3

root = Path(__file__).resolve().parents[1]
database = root / "tmp/local-preview/bidlens.db"
connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
connection.row_factory = sqlite3.Row


def rows(query):
    return [dict(row) for row in connection.execute(query)]


report = {
    "counts": {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in ("tenders", "requirements", "bidders", "bidder_uploaded_files", "bidder_documents", "evidence", "compliance_checks", "officer_decisions", "audit_events")},
    "tenders": rows("SELECT id, external_bid_id, status FROM tenders"),
    "bidders": rows("SELECT id, bidder_name, overall_status FROM bidders"),
    "evidence": rows("SELECT requirement_id, page, value, evidence_text, ambiguities_json FROM evidence"),
    "verdicts": rows("SELECT bidder_id, machine_status, COUNT(*) AS count FROM compliance_checks GROUP BY bidder_id,machine_status"),
    "officer_decisions": rows("SELECT action, old_status, new_status, remarks FROM officer_decisions"),
    "providers": rows("SELECT action, timestamp, details FROM audit_events WHERE action IN ('TENDER_EXTRACTION_STARTED','TENDER_EXTRACTION_COMPLETED','BIDDER_PROCESSING_STARTED','BIDDER_PROCESSING_COMPLETED')"),
    "localized": {table: rows(f"SELECT id, provenance FROM {table} WHERE provenance IS NOT NULL") for table in ("requirements", "evidence")},
}
originals = {}
for file in (root / "demo_files/bidders").rglob("*.pdf"):
    originals.setdefault(file.name, set()).add(hashlib.sha256(file.read_bytes()).hexdigest())
report["bidder_originals_unchanged"] = all(hashlib.sha256(Path(row["stored_path"]).read_bytes()).hexdigest() in originals.get(row["filename"], set()) for row in rows("SELECT filename, stored_path FROM bidder_uploaded_files"))
tender_hash = hashlib.sha256((root / "demo_files/tender/GEM_2026_B_7910945.pdf").read_bytes()).hexdigest()
report["tender_originals_unchanged"] = all(hashlib.sha256(Path(row["document_path"]).read_bytes()).hexdigest() == tender_hash for row in rows("SELECT document_path FROM tenders WHERE document_path IS NOT NULL"))
print(json.dumps(report, indent=2, ensure_ascii=False))
