import os
from pathlib import Path
import shutil
from uuid import uuid4

from fastapi import UploadFile


class StorageService:
    def __init__(self, root: str | Path | None = None):
        self.root = Path(root or os.getenv("UPLOAD_DIR", Path(__file__).resolve().parents[2] / "uploads"))
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, upload: UploadFile, namespace: str) -> Path:
        if not upload.filename or not upload.filename.lower().endswith(".pdf"):
            raise ValueError("Only PDF uploads are supported")
        target_dir = self.root / namespace
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{uuid4().hex}_{Path(upload.filename).name}"
        with target.open("wb") as destination:
            shutil.copyfileobj(upload.file, destination)
        return target

    def save_named(self, upload: UploadFile, namespace: str) -> Path:
        if not upload.filename or not upload.filename.lower().endswith(".pdf"):
            raise ValueError("Only PDF uploads are supported")
        target_dir = self.root / namespace
        target_dir.mkdir(parents=True, exist_ok=True)
        safe_name = Path(upload.filename).name
        target = target_dir / safe_name
        with target.open("wb") as destination:
            shutil.copyfileobj(upload.file, destination)
        return target
