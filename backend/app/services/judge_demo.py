"""Idempotent, non-destructive deployment seed using only audited demo assets."""
from datetime import datetime
import hashlib
import json
from pathlib import Path

from sqlalchemy import DateTime, select, text

from app.database.base import Base
from app.database.session import SessionLocal
from app.models import AuditEvent, Tender

DEMO_ID = "PREPROCESSED:GEM/2026/B/7910945"
ROOT = Path(__file__).resolve().parents[3]


def seed_judge_demo():
    payload = json.loads((ROOT / "backend/demo_assets/workspace.json").read_text(encoding="utf-8"))
    with SessionLocal() as db:
        if db.bind.dialect.name == "postgresql":
            db.execute(text("SELECT pg_advisory_xact_lock(7910945)"))
        existing = db.query(Tender).filter_by(external_bid_id=DEMO_ID).one_or_none()
        if existing:
            return existing.id
        # Absolute filesystem paths are generated on this server, never exposed
        # in the manifest or returned through public document endpoints.
        for relative, expected in payload["documents"].items():
            path = (ROOT / relative).resolve()
            if not path.is_relative_to(ROOT / "demo_files") or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise RuntimeError("Judge demo asset failed integrity verification")
        ids = {}
        order = ["tenders", "requirements", "bidders", "bidder_uploaded_files", "bidder_documents", "evidence", "compliance_checks", "registry_verifications", "officer_decisions", "clarification_requests", "audit_events"]
        for name in order:
            table = Base.metadata.tables[name]
            ids[name] = {}
            for original in payload["tables"][name]:
                row = {key: value for key, value in original.items() if key in table.c and key != "id"}
                for column in table.columns:
                    value = row.get(column.name)
                    if value is None:
                        continue
                    if column.foreign_keys:
                        target = next(iter(column.foreign_keys)).column.table.name
                        row[column.name] = ids[target][value]
                    elif isinstance(column.type, DateTime) and isinstance(value, str):
                        row[column.name] = datetime.fromisoformat(value)
                for key in ("stored_path", "document_path"):
                    if row.get(key):
                        row[key] = str(ROOT / row[key])
                if name == "tenders":
                    row["external_bid_id"] = DEMO_ID
                if name == "audit_events":
                    row["entity_id"] = None  # historic local identifiers are not deployed IDs
                result = db.execute(table.insert().values(**row))
                ids[name][original["id"]] = result.inserted_primary_key[0]
        tender_id = next(iter(ids["tenders"].values()))
        db.add(AuditEvent(tender_id=tender_id, action="PREPROCESSED_DEMO_IMPORTED", entity_type="Tender", entity_id=str(tender_id), details={"preprocessed": True, "description": payload["origin"], "registry": "SIMULATED"}))
        db.flush()
        # Same runtime rule engine and registry connectors as fresh processing.
        from app.api.evaluation import evaluate_tender
        evaluate_tender(tender_id, db)
        return tender_id
