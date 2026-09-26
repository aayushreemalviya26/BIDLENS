import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "sqlite:///./test-bidlens.db")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.api.auth import attempts, require_processing


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db, monkeypatch, tmp_path):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("PROTOTYPE_ADMIN_PASSWORD", "test-password")
    attempts.clear()
    def override_db():
        yield db
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[require_processing] = lambda: {"mode": "OFFLINE", "provider": "Ollama", "model": "qwen2.5:3b"}
    with TestClient(app) as test_client:
        assert test_client.post("/api/auth/login", json={"username": "admin", "password": "test-password"}).status_code == 200
        test_client.post("/api/auth/mode", json={"mode": "OFFLINE"})
        yield test_client
    app.dependency_overrides.clear()
