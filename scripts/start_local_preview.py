"""Run an isolated local preview without changing the existing public server."""
import os
from pathlib import Path
import sys

from dotenv import load_dotenv
import uvicorn

root = Path(__file__).resolve().parents[1]
load_dotenv(root / "backend" / ".env")
state = root / "tmp" / "local-preview"
state.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("DATABASE_URL", f"sqlite:///{(state / 'bidlens.db').as_posix()}")
os.environ.setdefault("UPLOAD_DIR", str(state / "uploads"))
os.environ.setdefault("FRONTEND_DIST_DIR", str(root / "frontend" / "dist-preview"))
os.environ.setdefault("APP_ENV", "local")
sys.path.insert(0, str(root / "backend"))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=int(os.getenv("PREVIEW_PORT", "8001")))
