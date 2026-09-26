import hashlib
from pathlib import Path

import httpx
import pytest

from app.api.auth import PrototypeSession, require_processing
from app.main import app
from app.services.llm_provider import GroqProvider, OllamaProvider, ProviderError, get_provider
from app.services.pdf_provenance import locate_evidence

ROOT = Path(__file__).resolve().parents[2]


def test_login_logout_and_persistent_mode(client, db):
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/tenders").status_code == 401
    assert client.get("/api/tenders/1/documents/original/file").status_code == 401
    for username, password in [("wrong", "test-password"), ("admin", "bad")]:
        assert client.post("/api/auth/login", json={"username": username, "password": password}).status_code == 401
    response = client.post("/api/auth/login", json={"username": "admin", "password": "test-password"})
    assert response.status_code == 200 and response.json()["mode"] is None
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=lax" in response.headers["set-cookie"]
    assert client.post("/api/auth/mode", json={"mode": "ONLINE"}).json()["provider"] == "Groq"
    db.expire_all()
    assert client.get("/api/auth/session").json()["mode"] == "ONLINE"
    token = client.cookies.get("bidlens_session")
    assert db.get(PrototypeSession, hashlib.sha256(token.encode()).hexdigest()).mode == "ONLINE"
    assert client.post("/api/auth/mode", json={"mode": "automatic"}).status_code == 422
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/session").status_code == 401


def test_csrf_and_online_missing_key(client, monkeypatch):
    assert client.post("/api/auth/mode", json={"mode": "ONLINE"}, headers={"Origin": "https://untrusted.example"}).status_code == 403
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    client.post("/api/auth/mode", json={"mode": "ONLINE"})
    response = client.post("/api/auth/health").json()
    assert not response["ready"] and "GROQ_API_KEY" in response["message"]
    app.dependency_overrides.pop(require_processing)
    assert client.post("/api/tenders/999/extract").status_code == 503
    assert client.get("/api/auth/session").json()["mode"] == "ONLINE"


def test_providers_route_only_to_explicit_provider(monkeypatch):
    calls = []
    monkeypatch.setenv("GROQ_API_KEY", "test-secret")
    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-120b")
    def post(url, **kwargs):
        calls.append((url, kwargs))
        payload = {"choices": [{"message": {"content": '{"ok": true}'}}]} if "groq.com" in url else {"message": {"content": "OK"}}
        return httpx.Response(200, json=payload, request=httpx.Request("POST", url))
    monkeypatch.setattr(httpx, "post", post)
    assert get_provider("ONLINE").chat([{"role": "user", "content": "JSON"}])["message"]["content"] == '{"ok": true}'
    assert calls[-1][0] == "https://api.groq.com/openai/v1/chat/completions"
    assert calls[-1][1]["json"]["model"] == "openai/gpt-oss-120b"
    assert get_provider("OFFLINE").chat([])["message"]["content"] == "OK"
    assert "127.0.0.1:11434" in calls[-1][0]
    assert "test-secret" not in str(GroqProvider().metadata())
    with pytest.raises(ProviderError):
        get_provider(None)


def test_provider_failure_does_not_fallback_or_leak_key(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-secret")
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: httpx.Response(429))
    with pytest.raises(ProviderError, match="HTTP 429") as error:
        GroqProvider().health()
    assert "test-secret" not in str(error.value)
    monkeypatch.setenv("OLLAMA_LOCAL_URL", "https://ollama.com")
    with pytest.raises(ProviderError, match="loopback"):
        OllamaProvider().health()


def test_original_evidence_localization_and_fallback():
    path = ROOT / "demo_files/bidders/bharat_compute/Local_Content_Declaration.pdf"
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    result = locate_evidence(path, 1, "15%")
    assert result["method"] == "exact_text"
    assert result["bounding_boxes"]
    assert all(0 <= box["x0"] < box["x1"] <= 1 and 0 <= box["y0"] < box["y1"] <= 1 for box in result["bounding_boxes"])
    assert locate_evidence(path, 1, "not present anywhere")["method"] == "unavailable"
    assert locate_evidence(path, 999, "15%")["bounding_boxes"] == []
    assert locate_evidence(path, 1, "35%", result)["bounding_boxes"] == []
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_production_recommends_online(client, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    assert client.get("/api/auth/session").json()["recommended_mode"] == "ONLINE"


def test_sources_stay_on_reported_page_and_category():
    from app.services.tender_ai_adapter import TenderAIAdapter
    items = [{"category": "GST", "applicable": True, "description": "GSTIN Number of bidder", "source": {"page": 11, "text": "GSTIN Number of bidder"}, "metadata": {}}]
    retrieval = [{"category": "GST", "results": [{"page": 11, "text": "14. Bidder has to submit a copy of Registration Certificate/GSTIN Number.", "chunk_id": "C1"}, {"page": 4, "text": "GSTIN Number of bidder", "chunk_id": "WRONG"}]}]
    result = TenderAIAdapter.attach_retrieved_sources(items, retrieval)[0]
    assert result["source"]["text"] == retrieval[0]["results"][0]["text"]
    assert result["description"] == "GSTIN Number of bidder"
    assert result["metadata"]["source_chunk_id"] == "C1"


def test_offline_health_missing_model_and_request_failure(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda url, **kw: httpx.Response(200, json={"models": []}, request=httpx.Request("GET", url)))
    with pytest.raises(ProviderError, match="Offline AI is currently unavailable"):
        OllamaProvider().health()


def test_override_reason_cannot_be_whitespace():
    from app.schemas.compliance import OverrideCreate
    with pytest.raises(ValueError):
        OverrideCreate(new_status="COMPLIANT", remarks="   ")
