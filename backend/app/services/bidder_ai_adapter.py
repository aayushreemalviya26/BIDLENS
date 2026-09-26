import json
import os
from pathlib import Path
import shutil
import tempfile

from .evidence_normalizer import EvidenceNormalizer
from .pipeline_runner import run_stage


class BidderAIAdapter:
    STAGES = ("extract.py", "classify.py", "segment.py", "chunk.py", "embed.py", "retrieve.py", "evidence.py")

    def __init__(self, pipeline_dir: Path | None = None):
        self.pipeline_dir = pipeline_dir or Path(__file__).resolve().parents[3] / "Bidder_doc"
        self.evidence_normalizer = EvidenceNormalizer()

    def normalize_outputs(self, documents: dict, evidence: dict) -> dict:
        return {"documents": documents.get("documents", []), "evidence": self.evidence_normalizer.normalize(evidence)}

    def run(self, pdf_path: str | Path, requirements: list[dict], bidder_id: str = "UNSPECIFIED", bidder_name: str = "Unspecified bidder") -> dict:
        bidder_id = getattr(self, "bidder_id", bidder_id)
        bidder_name = getattr(self, "bidder_name", bidder_name)
        with tempfile.TemporaryDirectory(prefix="bidlens-bidder-") as temp:
            work = Path(temp) / "Bidder_doc"
            shutil.copytree(self.pipeline_dir, work, ignore=shutil.ignore_patterns("data", "__pycache__"))
            data = work / "data"
            data.mkdir()
            shutil.copy2(Path(__file__).with_name("llm_provider.py"), work / "bidlens_llm.py")
            shutil.copy2(Path(__file__).with_name("embedding_provider.py"), work / "bidlens_embeddings.py")
            shutil.copy2(pdf_path, data / "bidder.pdf")
            (data / "requirements.json").write_text(json.dumps(requirements, ensure_ascii=False, indent=2), encoding="utf-8")
            (data / "bidder_metadata.json").write_text(json.dumps({"bidder_id": bidder_id, "bidder_name": bidder_name}, ensure_ascii=False, indent=2), encoding="utf-8")
            env = {
                **os.environ,
                "OLLAMA_HOST": os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_HOST", "http://localhost:11434")),
                "PYTHONIOENCODING": "utf-8",
                "BIDLENS_AI_MODE": getattr(self, "mode", "OFFLINE"),
            }
            for stage in self.STAGES:
                if getattr(self, "mode", "OFFLINE") == "OFFLINE":
                    env.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
                run_stage(stage, work, env)
            documents = json.loads((data / "bidder_documents.json").read_text(encoding="utf-8"))
            evidence = json.loads((data / "bidder_evidence.json").read_text(encoding="utf-8"))
            return self.normalize_outputs(documents, evidence)
