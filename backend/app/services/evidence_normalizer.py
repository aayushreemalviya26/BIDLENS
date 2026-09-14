class EvidenceNormalizer:
    def normalize(self, payload: dict) -> list[dict]:
        rows: list[dict] = []
        for result in payload.get("results", []):
            requirement_id = result.get("requirement_id")
            ambiguities = result.get("ambiguities") or []
            evidence_items = result.get("evidence") or []
            if not evidence_items:
                rows.append({"requirement_id": requirement_id, "document_id": None, "page": None, "field": None, "value": None, "unit": None, "evidence_text": None, "evidence_found": False, "ambiguities": ambiguities})
            for item in evidence_items:
                value = item.get("value")
                rows.append({
                    "requirement_id": requirement_id,
                    "document_id": item.get("document_id"),
                    "page": item.get("page"),
                    "field": item.get("field"),
                    "value": value,
                    "unit": item.get("unit") or None,
                    "evidence_text": item.get("evidence_text") or value,
                    "evidence_found": bool(result.get("evidence_found", True)),
                    "ambiguities": ambiguities,
                })
        return rows
