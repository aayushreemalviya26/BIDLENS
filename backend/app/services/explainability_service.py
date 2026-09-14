class ExplainabilityService:
    def build(self, requirement, evidence, verification, status: str, reason: str) -> dict:
        first = evidence[0] if evidence else None
        return {
            "explanation": reason,
            "tender_source": {"clause": requirement.source_clause, "page": requirement.source_page, "text": requirement.source_text},
            "bidder_source": None if first is None else {"document_id": first.document_id, "page": first.page, "field": first.field, "value": first.value, "text": first.evidence_text},
            "registry_source": None if verification is None else {"source": verification.source, "identifier": verification.identifier, "status": verification.status, "matched": verification.matched, "record": verification.registry_record_json, "discrepancies": verification.discrepancies_json},
            "rule": requirement.operator,
            "status": status,
        }
