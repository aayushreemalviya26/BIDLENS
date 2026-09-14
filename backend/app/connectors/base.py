import json
from pathlib import Path


class RegistryConnector:
    source = "REGISTRY"
    filename = "registry.json"
    identifier_field = "identifier"

    def __init__(self, registry_dir: str | Path | None = None):
        self.registry_dir = Path(registry_dir or Path(__file__).resolve().parents[2] / "mock_registry")

    def lookup(self, identifier: str, bidder_name: str | None = None) -> dict:
        records = json.loads((self.registry_dir / self.filename).read_text(encoding="utf-8"))
        normalized = self._normalize_identifier(identifier)
        record = next((item for item in records if self._normalize_identifier(str(item.get(self.identifier_field, ""))) == normalized), None)
        discrepancies: list[str] = []
        if record and bidder_name:
            registry_name = record.get("legal_name") or record.get("enterprise_name") or record.get("company_name")
            if registry_name and self._normalize_name(registry_name) != self._normalize_name(bidder_name):
                discrepancies.append(f'Entity mismatch: bidder "{bidder_name}" vs registry "{registry_name}"')
        active = record is not None and str(record.get("status", "ACTIVE")).upper() in {"ACTIVE", "VALID", "VERIFIED", "RECOGNISED", "RECOGNIZED"}
        matched = bool(record and not discrepancies and active)
        return {"source": self.source, "identifier": identifier, "status": "VERIFIED" if matched else ("NOT_FOUND" if not record else "MISMATCH"), "matched": matched, "registry_record": record or {}, "discrepancies": discrepancies or ([] if record else ["Identifier not found in simulated registry"])}

    @staticmethod
    def _normalize_identifier(value: str) -> str:
        return "".join(ch for ch in value.upper() if ch.isalnum())

    @staticmethod
    def _normalize_name(value: str) -> str:
        replacements = {"PRIVATE": "", "PVT": "", "LIMITED": "", "LTD": "", ".": ""}
        result = value.upper()
        for old, new in replacements.items():
            result = result.replace(old, new)
        return "".join(ch for ch in result if ch.isalnum())
