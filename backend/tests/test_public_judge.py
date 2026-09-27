from contextlib import contextmanager

from app.models import Bidder, ComplianceCheck, Evidence, Requirement, Tender
from app.services import judge_demo


def test_public_demo_scoped_reads_and_no_mutations(client, db, monkeypatch):
    @contextmanager
    def session():
        yield db
    monkeypatch.setattr(judge_demo, "SessionLocal", session)
    demo_id = judge_demo.seed_judge_demo()
    other = Tender(title="Private evaluation", external_bid_id="PRIVATE")
    db.add(other)
    db.commit()
    client.cookies.clear()
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("PUBLIC_JUDGE_DEMO", "true")
    assert client.get("/api/demo/access").json() == {"public_read_only": True}
    assert client.get("/api/demo/workspace").json()["tender_id"] == demo_id
    assert [t["id"] for t in client.get("/api/tenders").json()] == [demo_id]
    for suffix in ("", "/requirements", "/bidders", "/compliance-matrix", "/document-completeness", "/audit", "/documents/original/file"):
        assert client.get(f"/api/tenders/{demo_id}{suffix}").status_code == 200
        assert client.get(f"/api/tenders/{other.id}{suffix}").status_code == 404
    for row in db.query(Requirement).filter_by(tender_id=demo_id).all():
        assert client.get(f"/api/requirements/{row.id}/source").status_code == 200
    for row in db.query(Evidence).all():
        assert client.get(f"/api/evidence/{row.id}/source").status_code == 200
    for bidder in client.get(f"/api/tenders/{demo_id}/bidders").json():
        for file in bidder["uploaded_files"]:
            assert client.get(file["url"]).status_code == 200
    check = db.query(ComplianceCheck).first()
    assert client.get(f"/api/compliance/{check.id}/evidence").status_code == 200
    for path in ("/api/tenders", "/api/demo/reset", f"/api/tenders/{demo_id}/evaluate", f"/api/compliance/{check.id}/accept", f"/api/jobs/tender/{demo_id}"):
        assert client.post(path, json={}).status_code == 403
    assert client.get("/api/auth/session").status_code == 401
    assert client.post("/api/auth/mode", json={"mode":"ONLINE"}).status_code == 401
    assert client.get("/api/jobs/not-public").status_code == 401
    monkeypatch.setenv("PUBLIC_JUDGE_DEMO", "false")
    assert client.get("/api/tenders").status_code == 401
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("PUBLIC_JUDGE_DEMO", "true")
    assert client.get("/api/tenders").status_code == 401
