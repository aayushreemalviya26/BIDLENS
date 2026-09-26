"""Bounded background processing so proxy timeouts do not lose long AI runs."""
from datetime import datetime, timezone
import threading
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.database.base import Base
from app.database.session import SessionLocal, get_db
from .auth import require_processing
from .common import get_bidder, get_tender

router = APIRouter(tags=["processing jobs"])
guard = threading.Lock()


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    kind: Mapped[str] = mapped_column(String(20))
    target_id: Mapped[int] = mapped_column()
    status: Mapped[str] = mapped_column(String(20), default="RUNNING")
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


def run_job(job_id, ai):
    with SessionLocal() as db:
        job = db.get(ProcessingJob, job_id)
        try:
            if job.kind == "tender":
                from .tenders import extract_tender
                result = extract_tender(job.target_id, db, ai)
            else:
                from .bidders import process_bidder
                result = process_bidder(job.target_id, db, ai)
            job.result, job.status = result, "COMPLETED"
        except Exception as error:
            db.rollback()
            job = db.get(ProcessingJob, job_id)
            # Existing pipeline handlers provide sanitized user-facing errors.
            job.error = str(error.detail) if isinstance(error, HTTPException) else "Processing failed. Existing preprocessed demo remains available."
            job.status = "FAILED"
        db.commit()


@router.post("/jobs/{kind}/{target_id}", status_code=202)
def start_job(kind: str, target_id: int, background: BackgroundTasks, db: Session = Depends(get_db), ai=Depends(require_processing)):
    if kind not in {"tender", "bidder"}:
        raise HTTPException(400, "Unknown processing job")
    (get_tender if kind == "tender" else get_bidder)(db, target_id)
    with guard:
        if db.query(ProcessingJob).filter_by(status="RUNNING").first():
            raise HTTPException(409, "An AI job is already running. Please wait; the preprocessed demo is available.")
        job = ProcessingJob(id=str(uuid4()), kind=kind, target_id=target_id)
        db.add(job)
        db.commit()
    background.add_task(run_job, job.id, ai)
    return {"job_id": job.id, "status": "RUNNING"}


@router.get("/jobs/{job_id}")
def job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.get(ProcessingJob, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return {"job_id": job.id, "status": job.status, "result": job.result, "error": job.error}
