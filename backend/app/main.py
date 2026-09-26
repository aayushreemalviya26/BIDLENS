import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import audit, auth, bidders, demo, evaluation, jobs, sources, tenders
from app.database.init_db import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    from app.database.session import SessionLocal
    with SessionLocal() as db:
        db.query(jobs.ProcessingJob).filter_by(status="RUNNING").update({"status": "FAILED", "error": "Server restarted during processing. Please retry. Preprocessed demo is unaffected."})
        db.commit()
    if os.getenv("SEED_JUDGE_DEMO") == "true":
        from app.services.judge_demo import seed_judge_demo
        seed_judge_demo()
    yield


app = FastAPI(title="BIDLENS API", version="1.0.0", lifespan=lifespan)
origins = [
    item.strip()
    for item in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if item.strip()
]
origin_regex = os.getenv("CORS_ORIGIN_REGEX") or None
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.middleware("http")
async def check_origin(request: Request, call_next):
    origin = request.headers.get("origin")
    if request.method not in {"GET", "HEAD", "OPTIONS"} and origin:
        if origin not in origins and origin != str(request.base_url).rstrip("/"):
            return JSONResponse({"detail": "Request origin is not allowed."}, status_code=403)
    response = await call_next(request)
    if request.url.path.startswith("/api"):
        response.headers["Cache-Control"] = "no-store"
    return response


app.include_router(auth.router, prefix="/api")
for router in (tenders.router, bidders.router, evaluation.router, audit.router, demo.router, sources.router, jobs.router):
    app.include_router(router, prefix="/api", dependencies=[Depends(auth.require_session)])

@app.get("/health")
@app.get("/api/health")
def health():
    return {"status": "ok"}


frontend_dir = Path(os.getenv("FRONTEND_DIST_DIR", Path(__file__).resolve().parents[2] / "frontend" / "dist"))
if frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
