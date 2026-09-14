import re
from difflib import SequenceMatcher
from typing import Any


CATEGORY_DOCUMENTS = {
    "GST": "GST", "PAN / Income Tax": "PAN", "Udyam / MSME": "UDYAM",
    "Make in India / Local Content": "MII_LOCAL_CONTENT", "OEM Authorization": "OEM_AUTHORIZATION",
    "BIS / DPIIT": "BIS", "Startup India": "STARTUP_NSIC", "Blacklisting / Debarment": "DECLARATION",
}

HEADING_BY_CATEGORY = {
    "GST": "GST Registration",
    "PAN / Income Tax": "PAN / Income Tax",
    "Udyam / MSME": "Udyam / MSME Certificate",
    "Make in India / Local Content": "Make in India / Local Content",
    "OEM Authorization": "OEM Authorization",
    "BIS / DPIIT": "BIS Certification",
    "Startup India": "Startup India Registration",
    "Startup India / NSIC": "Startup India / NSIC Registration",
    "Blacklisting / Debarment": "Blacklisting / Debarment",
}


class RequirementNormalizer:
    """Normalizes supported tender language and deduplicates before persistence."""

    def __init__(self):
        self.stats = {"before": 0, "after": 0, "duplicates_removed": 0}

    def normalize(self, raw_items: list[dict[str, Any]], context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        context = context or {}
        candidates: list[dict[str, Any]] = []
        for group in raw_items:
            category = str(group.get("query") or group.get("category") or "Uncategorized")
            if group.get("status") == "not_found":
                candidates.append(self._canonical(category, category, None, False, context))
                continue
            for item in group.get("requirements") or [group]:
                description = str(item.get("requirement") or item.get("description") or "").strip()
                if description:
                    candidates.append(self._canonical(category, description, item.get("page"), True, context))

        self.stats["before"] = len(candidates)
        candidates = self._collapse_known_groups(candidates)
        deduped: list[dict[str, Any]] = []
        for item in candidates:
            if not any(self._is_duplicate(existing, item) for existing in deduped):
                deduped.append(item)
        for sequence, item in enumerate(deduped, start=1):
            item["requirement_id"] = f"REQ{sequence:03d}"
        self.stats.update(after=len(deduped), duplicates_removed=self.stats["before"] - len(deduped))
        return deduped

    def _canonical(self, category: str, description: str, page: int | None, applicable: bool, context: dict[str, Any]) -> dict[str, Any]:
        operator, required_value, unit, metadata = "MANUAL_REVIEW", None, None, {}
        document_type = CATEGORY_DOCUMENTS.get(category)
        text = description.casefold()
        local = re.search(r"minimum\s+(\d+(?:\.\d+)?)%\s+and\s+(\d+(?:\.\d+)?)%\s+local content", text)
        turnover = re.search(r"(?:minimum\s+)?(?:average annual )?turnover[^\d]*(\d+(?:\.\d+)?)\s*(lakh|crore)?", text)
        turnover_percent = re.search(r"turnover\s+of\s+(\d+(?:\.\d+)?)%\s+of\s+the\s+estimated", text)
        estimate = context.get("estimated_bid_value")
        if local:
            operator, unit = "LOCAL_CONTENT_CLASSIFICATION", "PERCENT"
            metadata = {"class_1_threshold": float(local.group(1)), "class_2_threshold": float(local.group(2))}
        elif turnover_percent and estimate:
            percent = float(turnover_percent.group(1))
            operator, required_value, unit, document_type = "GREATER_THAN_OR_EQUAL", float(estimate) * percent / 100, "INR", "TURNOVER"
            metadata = {"percentage_of_estimated_bid_value": percent, "estimated_bid_value": float(estimate)}
        elif turnover and ("minimum" in text or "average annual" in text) and not ("%" in text or "estimated cost" in text):
            multiplier = {"lakh": 100_000, "crore": 10_000_000}.get(turnover.group(2), 1)
            operator, required_value, unit, document_type = "GREATER_THAN_OR_EQUAL", float(turnover.group(1)) * multiplier, "INR", "TURNOVER"
        elif category in {"GST", "PAN / Income Tax", "Udyam / MSME", "BIS / DPIIT"}:
            operator = "EXACT_IDENTIFIER_MATCH"
        elif category == "OEM Authorization":
            operator = "BIDDER_NAME_MATCH"
        elif "make in india declaration" in text or "local content declaration" in text:
            operator = "EXISTS"
        elif category == "Tender-Specific Eligibility" and any(token in text for token in ("similar category", "similar works", "single order", "two orders", "three orders", "experience certificate")):
            operator, document_type = "EXISTS", "EXPERIENCE"
        elif any(token in text for token in ("certificate", "gstin", "pan card", "licence", "license", "documentary evidence", "declaration", "details", "financial standing")):
            operator = "EXISTS"
        return {
            "requirement_id": "", "name": self._heading(category, description, document_type), "category": category,
            "description": description, "operator": "MANUAL_REVIEW" if not applicable else operator,
            "required_value": required_value, "unit": unit, "mandatory": applicable, "required_document_type": document_type,
            "source": {"clause": None, "page": page, "text": description if applicable else None},
            "confidence": None, "approved": False, "applicable": applicable, "metadata": metadata,
        }

    @staticmethod
    def _heading(category: str, description: str, document_type: str | None) -> str:
        text = description.casefold()
        if "turnover" in text:
            return "Minimum OEM Turnover" if "oem" in text else "Minimum Bidder Turnover"
        if category in HEADING_BY_CATEGORY:
            return HEADING_BY_CATEGORY[category]
        if document_type == "EXPERIENCE" or "experience" in text:
            return "Similar Supply / Work Experience"
        if "service centre" in text or "service center" in text:
            return "Service Centre Details"
        if "financial standing" in text or "net worth" in text:
            return "Financial Standing"
        if "malicious code" in text or "backdoor" in text:
            return "Malicious Code Declaration"
        if "past performance" in text:
            return "Past Performance"
        words = re.findall(r"[A-Za-z0-9%]+", description)
        boilerplate = {"bidder", "must", "shall", "submit", "provide", "the", "a", "an", "valid", "copy", "of", "its", "their"}
        concise = [word for word in words if word.casefold() not in boilerplate][:7]
        if len(concise) < 3:
            concise = words[:7]
        return " ".join(concise).strip() or category

    @staticmethod
    def _collapse_known_groups(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result, experience = [], []
        udyam_added = False
        has_structured_local = any(item["operator"] == "LOCAL_CONTENT_CLASSIFICATION" for item in items)
        for item in items:
            if item["category"] == "Udyam / MSME" and item["applicable"]:
                if udyam_added:
                    continue
                item.update(name="Valid Udyam registration", description="The bidder must submit a valid Udyam registration certificate.", operator="EXACT_IDENTIFIER_MATCH", required_document_type="UDYAM")
                item["source"]["text"] = item["description"]
                udyam_added = True
            if item["category"] == "Make in India / Local Content" and has_structured_local and item["operator"] == "MANUAL_REVIEW":
                continue
            if item["category"] == "Tender-Specific Eligibility" and item["required_document_type"] == "EXPERIENCE":
                experience.append(item)
                continue
            result.append(item)
        if experience:
            first = experience[0]
            first.update(name="Similar supply/work experience", description="The bidder must submit documentary evidence of qualifying similar supply/work experience during the last 10 financial years.", operator="EXISTS", required_document_type="EXPERIENCE")
            first["source"]["text"] = " ".join(item["source"]["text"] or "" for item in experience)
            result.append(first)
        return result

    @staticmethod
    def _is_duplicate(left: dict[str, Any], right: dict[str, Any]) -> bool:
        if (left["category"], left["applicable"], left["operator"], left.get("required_value"), left["source"].get("page")) != (right["category"], right["applicable"], right["operator"], right.get("required_value"), right["source"].get("page")):
            return False
        a = re.sub(r"\W+", " ", left["description"].casefold()).strip()
        b = re.sub(r"\W+", " ", right["description"].casefold()).strip()
        return a == b or SequenceMatcher(None, a, b).ratio() >= 0.82
