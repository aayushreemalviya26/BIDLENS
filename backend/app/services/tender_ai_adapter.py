import json
import os
import re
from pathlib import Path
import shutil
import tempfile

from pypdf import PdfReader

from .requirement_normalizer import RequirementNormalizer
from .pipeline_runner import run_stage


class TenderAIAdapter:
    STAGES = ("extract_text.py", "clean_text.py", "chunk_tender.py", "embed_chunk.py", "embed_queries.py", "retrive_chunks.py", "extract_requirements.py")

    def __init__(self, pipeline_dir: Path | None = None, normalizer: RequirementNormalizer | None = None):
        self.pipeline_dir = pipeline_dir or Path(__file__).resolve().parents[3] / "Extraction_pipeline"
        self.normalizer = normalizer or RequirementNormalizer()

    def normalize_output(self, payload: list[dict], context: dict | None = None) -> list[dict]:
        return self.normalizer.normalize(payload, context)

    @staticmethod
    def attach_retrieved_sources(requirements, retrieval):
        """Keep actual retrieved text, separately from the model's paraphrase.

        A chunk is eligible only on the model-reported page, in its own category's
        retrieval set, with substantive lexical overlap. Otherwise retain the
        model span and let the viewer explicitly report localization failure.
        """
        stop = {"the", "of", "a", "and", "or", "to", "in", "for", "is", "as", "be", "by", "on", "with", "shall", "must", "bidder", "bidders", "should", "submit", "certificate", "required", "valid", "registration"}
        def terms(text):
            return set(re.findall(r"[a-z0-9]+", text.casefold())) - stop
        for item in requirements:
            source = item.get("source") or {}
            if not item.get("applicable") or not source.get("page"):
                continue
            wanted = terms(source.get("text") or item["description"])
            candidates = [chunk for group in retrieval if group.get("category") == item["category"] for chunk in group.get("results", []) if chunk.get("page") == source["page"]]
            ranked = sorted(candidates, key=lambda chunk: (len(wanted & terms(chunk.get("text", ""))) / max(len(wanted), 1), -len(chunk.get("text", ""))), reverse=True)
            if ranked and wanted and len(wanted & terms(ranked[0].get("text", ""))) / len(wanted) >= .6:
                chunk = ranked[0]
                source["text"] = chunk["text"]
                item.setdefault("metadata", {}).update(source_kind="retrieved_chunk", source_chunk_id=chunk.get("chunk_id"))
        return requirements

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
            shutil.copy2(Path(__file__).with_name("llm_provider.py"), work / "bidlens_llm.py")
            shutil.copy2(Path(__file__).with_name("embedding_provider.py"), work / "bidlens_embeddings.py")
            (work / "extracted").mkdir()
            shutil.copy2(pdf_path, work / "data" / "tender.pdf")
            # The existing pipeline treats its curated query set as a checked-in input.
            shutil.copy2(self.pipeline_dir / "extracted" / "queries.json", work / "extracted" / "queries.json")
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
            payload = json.loads((work / "extracted" / "extracted_requirements.json").read_text(encoding="utf-8"))
            if any(item.get("status") == "error" for item in payload):
                raise RuntimeError("Requirement extraction contained errors; existing checklist preserved. Retry processing.")
            requirements = self.normalize_output(payload, self._document_context(pdf_path))
            retrieval = json.loads((work / "extracted" / "retrieved_chunks.json").read_text(encoding="utf-8"))
            return self.attach_retrieved_sources(requirements, retrieval)
