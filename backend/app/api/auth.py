"""Temporary single-officer authentication, not a production identity system."""
import hashlib
import hmac
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.database.base import Base
from app.database.session import get_db
from app.services.llm_provider import ProviderError, get_provider

COOKIE = "bidlens_session"
router = APIRouter(prefix="/auth", tags=["prototype authentication"])
attempts = {}
attempt_lock = Lock()


class PrototypeSession(Base):
    __tablename__ = "prototype_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    username: Mapped[str] = mapped_column(String(200))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    mode: Mapped[str | None] = mapped_column(String(10), nullable=True)


def require_session(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get(COOKIE, "")
    session = db.get(PrototypeSession, hashlib.sha256(token.encode()).hexdigest()) if token else None
    if not session or session.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
        raise HTTPException(401, "Sign in to BidLens.")
    request.state.auth_session = session
    return session


def require_processing(request: Request, db: Session = Depends(get_db)):
    session = None
    token = request.cookies.get(COOKIE, "")
    if token:
        session = db.get(PrototypeSession, hashlib.sha256(token.encode()).hexdigest())
        if session and session.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
            session = None
    public_judge = os.getenv("APP_ENV") == "production" and os.getenv("PUBLIC_JUDGE_DEMO", "false") == "true"
    if session is None and not public_judge:
        raise HTTPException(401, "Sign in to BidLens.")
    mode = session.mode if session else "ONLINE"
    try:
        provider = get_provider(mode)
        provider.health()
        request.state.ai = provider.metadata()
        return provider.metadata()
    except ProviderError as error:
        raise HTTPException(503, str(error)) from error


def profile(session):
    metadata = get_provider(session.mode).metadata() if session.mode else {}
    return {"name": "Admin", "username": session.username, "role": "Procurement Officer", "prototype": "BidLens", "mode": session.mode, **metadata, "recommended_mode": "ONLINE" if os.getenv("APP_ENV") == "production" else "OFFLINE", "hosted": os.getenv("APP_ENV") == "production"}


class Login(BaseModel):
    username: str = Field(max_length=200)
    password: str = Field(max_length=500)


@router.post("/login")
def login(payload: Login, request: Request, response: Response, db: Session = Depends(get_db)):
    address = request.client.host if request.client else "unknown"
    now = time.monotonic()
    with attempt_lock:
        recent = [at for at in attempts.get(address, []) if now - at < 60]
        if len(recent) >= 10:
            raise HTTPException(429, "Too many sign-in attempts. Retry in one minute.")
        attempts[address] = recent + [now]
    username = os.getenv("PROTOTYPE_ADMIN_USERNAME", "admin")
    password = os.getenv("PROTOTYPE_ADMIN_PASSWORD", "")
    if not password:
        raise HTTPException(503, "Prototype login is not configured on the backend.")
    if not (hmac.compare_digest(payload.username.encode(), username.encode()) & hmac.compare_digest(payload.password.encode(), password.encode())):
        raise HTTPException(401, "Invalid username or password.")
    token = secrets.token_urlsafe(32)
    session = PrototypeSession(token_hash=hashlib.sha256(token.encode()).hexdigest(), username=username, expires_at=datetime.now(timezone.utc) + timedelta(hours=12))
    if os.getenv("APP_ENV") == "production":
        session.mode = "ONLINE"
    db.add(session)
    db.commit()
    response.set_cookie(COOKIE, token, httponly=True, secure=os.getenv("COOKIE_SECURE", "true" if os.getenv("APP_ENV") == "production" else "false") == "true", samesite="lax", max_age=43200, path="/")
    response.headers["Cache-Control"] = "no-store"
    return profile(session)


@router.get("/session")
def read_session(response: Response, session=Depends(require_session)):
    response.headers["Cache-Control"] = "no-store"
    return profile(session)


@router.post("/logout")
def logout(response: Response, db: Session = Depends(get_db), session=Depends(require_session)):
    db.delete(session)
    db.commit()
    response.delete_cookie(COOKIE, path="/")
    return {"logged_out": True}


class Mode(BaseModel):
    mode: Literal["OFFLINE", "ONLINE"]


@router.post("/mode")
def set_mode(payload: Mode, db: Session = Depends(get_db), session=Depends(require_session)):
    if os.getenv("APP_ENV") == "production" and payload.mode == "OFFLINE":
        raise HTTPException(400, "Offline mode is local-only. This hosted demo uses Groq.")
    session.mode = payload.mode
    db.commit()
    return profile(session)


@router.post("/health")
def ai_health(session=Depends(require_session)):
    try:
        provider = get_provider(session.mode)
        provider.health()
        return {"ready": True, **provider.metadata(), "message": "Offline AI Ready" if session.mode == "OFFLINE" else "Online AI Ready"}
    except ProviderError as error:
        return {"ready": False, "message": str(error)}
