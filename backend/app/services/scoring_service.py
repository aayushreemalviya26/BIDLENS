class ScoringService:
    def calculate(self, checks: list) -> tuple[float, str, str]:
        applicable = [c for c in checks if c.required == "MANDATORY" and c.effective_status not in {"NOT_APPLICABLE", "NOT_EVALUATED"}]
        passed = sum(c.effective_status == "COMPLIANT" for c in applicable)
        score = round((passed / len(applicable)) * 100, 2) if applicable else 0.0
        if any(c.required == "MANDATORY" and c.effective_status == "NON_COMPLIANT" for c in checks):
            return score, "HIGH", "NON_COMPLIANT"
        if any(c.effective_status in {"NEEDS_REVIEW", "NOT_EVALUATED"} for c in checks):
            return score, "MEDIUM", "NEEDS_REVIEW"
        return score, "LOW", "COMPLIANT"
