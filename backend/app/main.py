import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import audit, bidders, demo, evaluation, tenders
from app.database.init_db import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="BIDLENS API", version="1.0.0", lifespan=lifespan)
origins = [
    item.strip()
    for item in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if item.strip()
]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(tenders.router, prefix="/api")
app.include_router(bidders.router, prefix="/api")
app.include_router(evaluation.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(demo.router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok"}
