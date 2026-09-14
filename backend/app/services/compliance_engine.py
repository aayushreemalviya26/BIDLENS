from datetime import date, datetime
import re


STATUSES = {"COMPLIANT", "NON_COMPLIANT", "NEEDS_REVIEW", "NOT_APPLICABLE", "NOT_EVALUATED"}


class ComplianceEngine:
    def evaluate(self, requirement, evidence: list, verification=None, bidder_name: str | None = None) -> dict:
        operator = requirement.operator
        if not requirement.applicable:
            return self._result("NOT_APPLICABLE", "The tender does not contain this requirement.", None)
        if not requirement.approved:
            return self._result("NOT_EVALUATED", "Requirement has not been approved for evaluation.", None)
        found_items = [item for item in evidence if item.evidence_found and item.value not in (None, "")]
        if operator == "NOT_EXISTS" and not found_items:
            return self._result("COMPLIANT", "No prohibited evidence or registry entry was found.", None)
        if not found_items:
            ambiguities = [text for item in evidence for text in (item.ambiguities_json or [])]
            reason = "Required evidence is missing." + (f" {'; '.join(ambiguities)}" if ambiguities else "")
            return self._result("NEEDS_REVIEW", reason, None)
        if any(item.ambiguities_json for item in evidence):
            return self._result("NEEDS_REVIEW", "Evidence is ambiguous or conflicting.", self._display(found_items))

        values = [item.value for item in found_items]
        numeric = self._first_number(values)
        result = None
        if operator == "MANUAL_REVIEW":
            return self._result("NEEDS_REVIEW", "This requirement was not safely normalized and requires officer review.", self._display(found_items))
        if operator == "EXISTS":
            result = True
        elif operator == "NOT_EXISTS":
            result = not found_items
        elif operator in {"EQUALS", "EXACT_IDENTIFIER_MATCH", "ENTITY_MATCH", "REGISTRY_STATUS"}:
            if operator in {"EXACT_IDENTIFIER_MATCH", "ENTITY_MATCH", "REGISTRY_STATUS"}:
                result = bool(verification and verification.matched)
            else:
                result = any(str(v).casefold() == str(requirement.required_value).casefold() for v in values)
        elif operator == "NOT_EQUALS":
            result = all(str(v).casefold() != str(requirement.required_value).casefold() for v in values)
        elif operator in {"GREATER_THAN", "GREATER_THAN_OR_EQUAL", "LESS_THAN", "LESS_THAN_OR_EQUAL"}:
            if numeric is None or requirement.required_value is None:
                return self._result("NEEDS_REVIEW", "A numeric comparison could not be completed from the extracted evidence.", self._display(found_items))
            expected = float(requirement.required_value)
            result = {"GREATER_THAN": numeric > expected, "GREATER_THAN_OR_EQUAL": numeric >= expected, "LESS_THAN": numeric < expected, "LESS_THAN_OR_EQUAL": numeric <= expected}[operator]
        elif operator in {"MUST_BE_TRUE", "MUST_BE_FALSE"}:
            truth = any(str(v).strip().casefold() in {"true", "yes", "active", "valid", "filed"} for v in values)
            result = truth if operator == "MUST_BE_TRUE" else not truth
        elif operator == "DATE_VALID":
            parsed = self._first_date(values)
            if parsed is None:
                return self._result("NEEDS_REVIEW", "No unambiguous validity date was extracted.", self._display(found_items))
            result = parsed >= date.today()
        elif operator == "LOCAL_CONTENT_CLASSIFICATION":
            if numeric is None:
                return self._result("NEEDS_REVIEW", "Local-content percentage was not extracted.", self._display(found_items))
            thresholds = requirement.rule_metadata or {}
            class_2 = float(thresholds.get("class_2_threshold", 20))
            class_1 = float(thresholds.get("class_1_threshold", 50))
            result = numeric >= class_2
            classification = "Class 1" if numeric >= class_1 else ("Class 2" if numeric >= class_2 else "Non-local")
            reason = f"Extracted local content is {numeric:g}%, classified as {classification}; minimum qualifying threshold is {class_2:g}%."
            return self._result("COMPLIANT" if result else "NON_COMPLIANT", reason, f"{numeric:g}%")
        elif operator == "BIDDER_NAME_MATCH":
            if not bidder_name:
                return self._result("NEEDS_REVIEW", "The registered bidder name is unavailable for entity matching.", self._display(found_items))
            expected = self._normalize_name(bidder_name)
            recipient_items = [item for item in found_items if any(token in (item.field or "").casefold() for token in ("authorized bidder", "authorised bidder", "recipient", "dealer name"))]
            if not recipient_items:
                recipient_items = [item for item in found_items if (item.field or "").strip().casefold() in {"bidder name", "dealer"}]
            candidate_values = [self._normalize_name(value) for item in recipient_items for value in (item.value, item.evidence_text) if value]
            if not candidate_values:
                return self._result("NEEDS_REVIEW", "The authorization recipient was not extracted unambiguously.", self._display(found_items))
            result = any(expected and expected in candidate for candidate in candidate_values)
            reason = "The authorization names the registered bidder." if result else "The authorization recipient does not unambiguously match the registered bidder name."
            return self._result("COMPLIANT" if result else "NEEDS_REVIEW", reason, self._display(found_items))
        else:
            return self._result("NEEDS_REVIEW", f"Unsupported operator {operator} requires manual review.", self._display(found_items))

        if operator in {"EXACT_IDENTIFIER_MATCH", "ENTITY_MATCH", "REGISTRY_STATUS"} and verification is None:
            return self._result("NEEDS_REVIEW", "Registry verification is unavailable.", self._display(found_items))
        reason = f"Deterministic rule {operator} {'passed' if result else 'failed'}."
        return self._result("COMPLIANT" if result else "NON_COMPLIANT", reason, self._display(found_items))

    @staticmethod
    def _result(status, reason, found):
        return {"status": status, "reason": reason, "found": found}

    @staticmethod
    def _display(items):
        return "; ".join(f"{item.field}: {item.value}" for item in items)

    @staticmethod
    def _first_number(values):
        for value in values:
            match = re.search(r"[-+]?\d[\d,]*(?:\.\d+)?", str(value))
            if match:
                number = float(match.group().replace(",", ""))
                lowered = str(value).casefold()
                if "crore" in lowered:
                    number *= 10_000_000
                elif "lakh" in lowered:
                    number *= 100_000
                return number
        return None

    @staticmethod
    def _first_date(values):
        for value in values:
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
                try:
                    return datetime.strptime(str(value).strip(), fmt).date()
                except ValueError:
                    pass
        return None

    @staticmethod
    def _normalize_name(value):
        text = str(value).upper()
        for token in ("PRIVATE", "PVT", "LIMITED", "LTD"):
            text = text.replace(token, "")
        return "".join(ch for ch in text if ch.isalnum())
