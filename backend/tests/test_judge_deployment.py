import sys

import numpy as np

from app.models import Bidder, ComplianceCheck, Tender
from app.services import judge_demo
from app.services.embedding_provider import SentenceTransformer


def test_seed_is_idempotent_and_documents_work(client, db, monkeypatch):
    # Borrow the test transaction without closing its externally owned session.
    from contextlib import contextmanager
    @contextmanager
    def session():
        yield db
    monkeypatch.setattr(judge_demo, "SessionLocal", session)
    first = judge_demo.seed_judge_demo()
    second = judge_demo.seed_judge_demo()
    assert first == second
    assert db.query(Tender).count() == 1
    assert db.query(Bidder).count() == 3
    statuses = {row.machine_status for row in db.query(ComplianceCheck).all()}
    assert {"COMPLIANT", "NON_COMPLIANT", "NEEDS_REVIEW", "NOT_APPLICABLE"} <= statuses
    assert client.get("/api/demo/workspace").json()["tender_id"] == first
    assert client.get(f"/api/tenders/{first}/documents/original/file").headers["content-type"] == "application/pdf"
    for bidder in client.get(f"/api/tenders/{first}/bidders").json():
        for document in bidder["uploaded_files"]:
            assert client.get(document["url"]).status_code == 200
    for check in db.query(ComplianceCheck).all():
        response = client.get(f"/api/compliance/{check.id}/evidence")
        assert response.status_code == 200
    assert client.post(f"/api/tenders/{first}/evaluate").status_code == 200
    assert len(client.get(f"/api/tenders/{first}/compliance-matrix").json()["bidders"]) == 3


def test_hosted_offline_and_reset_disabled(client, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    assert client.post("/api/auth/mode", json={"mode": "OFFLINE"}).status_code == 400
    assert client.post("/api/demo/reset").status_code == 403


def test_lexical_vectors_are_deterministic_without_model_loading(monkeypatch):
    monkeypatch.setenv("BIDLENS_RETRIEVAL", "lexical")
    model = SentenceTransformer("ignored")
    assert model.local is None
    vectors = model.encode(["GST registration certificate", "OEM turnover", "GST registration certificate"])
    assert np.array_equal(vectors[0], vectors[2])
    assert np.dot(vectors[0], vectors[2]) > np.dot(vectors[0], vectors[1])
