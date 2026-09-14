import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from pypdf import PdfReader

from .requirement_normalizer import RequirementNormalizer


class TenderAIAdapter:
    STAGES = ("extract_text.py", "clean_text.py", "chunk_tender.py", "embed_chunk.py", "embed_queries.py", "retrive_chunks.py", "extract_requirements.py")

    def __init__(self, pipeline_dir: Path | None = None, normalizer: RequirementNormalizer | None = None):
        self.pipeline_dir = pipeline_dir or Path(__file__).resolve().parents[3] / "Extraction_pipeline"
        self.normalizer = normalizer or RequirementNormalizer()

    def normalize_output(self, payload: list[dict], context: dict | None = None) -> list[dict]:
        return self.normalizer.normalize(payload, context)

    @staticmethod
    def _document_context(pdf_path: str | Path) -> dict:
        text = "\n".join((page.extract_text() or "") for page in PdfReader(str(pdf_path)).pages)
        match = __import__("re").search(r"Estimated\s+Bid\s+Value\s*[\r\n ]+(\d[\d,]*)", text, __import__("re").IGNORECASE)
        return {"estimated_bid_value": float(match.group(1).replace(",", ""))} if match else {}

    def run(self, pdf_path: str | Path) -> list[dict]:
        with tempfile.TemporaryDirectory(prefix="bidlens-tender-") as temp:
            work = Path(temp) / "Extraction_pipeline"
            shutil.copytree(self.pipeline_dir, work, ignore=shutil.ignore_patterns("data", "extracted", "__pycache__"))
            (work / "data").mkdir()
            (work / "extracted").mkdir()
            shutil.copy2(pdf_path, work / "data" / "tender.pdf")
            # The existing pipeline treats its curated query set as a checked-in input.
            shutil.copy2(self.pipeline_dir / "extracted" / "queries.json", work / "extracted" / "queries.json")
            env = {
                **os.environ,
                "OLLAMA_HOST": os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_HOST", "http://localhost:11434")),
                "PYTHONIOENCODING": "utf-8",
                "HF_HUB_OFFLINE": "1",
                "TRANSFORMERS_OFFLINE": "1",
            }
            for stage in self.STAGES:
                subprocess.run([sys.executable, stage], cwd=work, env=env, check=True)
            payload = json.loads((work / "extracted" / "extracted_requirements.json").read_text(encoding="utf-8"))
            return self.normalize_output(payload, self._document_context(pdf_path))
