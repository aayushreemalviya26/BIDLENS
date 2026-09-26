"""Read-only PDF localization. Rectangles are normalized to the displayed page."""
import hashlib
import re
from pathlib import Path

import pymupdf as fitz


def locate_evidence(path, page_number, evidence_text, stored=None):
    result = {"page_number": page_number, "evidence_text": evidence_text or "", "bounding_boxes": [], "method": "unavailable", "message": "Exact highlight unavailable"}
    if not path or not Path(path).is_file() or not page_number or not evidence_text:
        return result
    fingerprint = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if stored and stored.get("sha256") == fingerprint and stored.get("page_number") == page_number and stored.get("evidence_text") == evidence_text:
        return stored
    result["sha256"] = fingerprint
    try:
        with fitz.open(path) as pdf:
            if not 1 <= page_number <= len(pdf):
                return result
            page = pdf[page_number - 1]
            text = " ".join(evidence_text.split())
            rectangles = page.search_for(text)
            method = "exact_text"
            if not rectangles:
                # Match complete word sequences with punctuation/spacing normalized.
                words = page.get_text("words", sort=True)
                normalize = lambda value: re.sub(r"\W+", "", value.casefold())
                tokens = [(normalize(word[4]), word) for word in words if normalize(word[4])]
                target = [normalize(word) for word in text.split() if normalize(word)]
                for start in range(len(tokens) - len(target) + 1):
                    if target and [token for token, _ in tokens[start:start + len(target)]] == target:
                        rectangles.extend(fitz.Rect(word[:4]) for _, word in tokens[start:start + len(target)])
                method = "normalized_text"
            if not rectangles:
                # Only highlight a literal source paragraph fragment, never a fuzzy box.
                fragments = [part.strip() for part in re.split(r"[\n;]|(?<=[.!?])\s+", evidence_text) if len(part.split()) >= 6]
                for fragment in sorted(fragments, key=len, reverse=True):
                    rectangles = page.search_for(" ".join(fragment.split()))
                    if rectangles:
                        result["matched_text"] = fragment
                        method = "chunk"
                        break
            width, height = page.rect.width, page.rect.height
            for rect in rectangles:
                rect = rect * page.rotation_matrix
                result["bounding_boxes"].append({"x0": max(0, rect.x0 / width), "y0": max(0, rect.y0 / height), "x1": min(1, rect.x1 / width), "y1": min(1, rect.y1 / height)})
            if rectangles:
                result.update(method=method, message="Source paragraph highlighted; exact full span unavailable" if method == "chunk" else "Exact evidence highlighted")
    except (RuntimeError, ValueError):
        pass
    return result
