import json
import re
from pathlib import Path

from ollama import chat


INPUT = Path("data/bidder_pages.json")
OUTPUT = Path("data/bidder_classified.json")

MODEL = "qwen2.5:3b"


CATEGORIES = [
    "GENERAL",
    "EMPTY",
    "CIN",
    "UDYAM",
    "GST",
    "PAN",
    "STATUTORY",
    "EXPERIENCE",
    "TURNOVER",
    "NET_WORTH",
    "CA_CERTIFICATE",
    "BANK",
    "EMD",
    "EPBG",
    "OEM_AUTHORIZATION",
    "MII_LOCAL_CONTENT",
    "BIS",
    "STARTUP_NSIC",
    "DIGILOCKER",
    "TECHNICAL",
    "DECLARATION",
    "SUPPORTING_DOCUMENT",
    "OTHER"
]


# ------------------------------------------------------------------
# Deterministic high-confidence heading rules
# ------------------------------------------------------------------

HEADING_RULES = [

    (
        "DIGILOCKER",
        [
            r"\bdigilocker\b",
            r"\bdigilocker\s+document\b",
            r"\bdocument\s+verification\s+note\b"
        ]
    ),

    (
        "OEM_AUTHORIZATION",
        [
            r"\boem\s+authori[sz]ation\b",
            r"\boem\s+authori[sz]ation\s+certificate\b",
            r"\bauthori[sz]ed\s+dealer\b",
            r"\bmanufacturer\s+authori[sz]ation\b"
        ]
    ),

    (
        "STARTUP_NSIC",
        [
            r"\bstartup\s+india\b.*\bnsic\b",
            r"\bnsic\b.*\bstartup\s+india\b",
            r"\bnsic\s+registration\b",
            r"\bstartup\s+india\s+.*registration\b"
        ]
    ),

    (
        "MII_LOCAL_CONTENT",
        [
            r"\bmake\s+in\s+india\b",
            r"\blocal\s+content\s+declaration\b",
            r"\bpercentage\s+of\s+local\s+content\b",
            r"\bclass[- ]?1\s+local\s+supplier\b",
            r"\bclass[- ]?2\s+local\s+supplier\b"
        ]
    ),

    (
        "GST",
        [
            r"\bgst\s+registration\s+certificate\b",
            r"\bform\s+gst\s+reg[- ]?06\b"
        ]
    ),

    (
        "UDYAM",
        [
            r"\budyam\s+registration\s+certificate\b",
            r"\budyam\s+registration\s+number\b"
        ]
    ),

    (
        "PAN",
        [
            r"\bpan\s+card\b",
            r"\bincome\s+tax\s+compliance\b"
        ]
    ),

    (
        "CIN",
        [
            r"\bcertificate\s+of\s+incorporation\b",
            r"\bcin\s+[a-z0-9]+"
        ]
    ),

    (
        "TURNOVER",
        [
            r"\bturnover\s+certificate\b",
            r"\baudited\s+turnover\b"
        ]
    ),

    (
        "NET_WORTH",
        [
            r"\bfinancial standing certificate\b",
            r"\bpositive net worth\b",
            r"\bnet worth certificate\b"
        ]
    ),

    (
        "BIS",
        [
            r"\bbis\s+licen[cs]e\b",
            r"\bbis\s+(?:registration|certificate|certification)\b",
            r"\bbureau\s+of\s+indian\s+standards\b"
        ]
    ),

    (
        "TECHNICAL",
        [
            r"\btechnical compliance certificate\b",
            r"\btechnical specification sheet\b",
            r"\bbill of quantities\b"
        ]
    ),

    (
        "STATUTORY",
        [
            r"\biso 9001\b",
            r"\bquality management system certificate\b"
        ]
    ),

    (
        "SUPPORTING_DOCUMENT",
        [
            r"\bservice centre details\b",
            r"\bservice center details\b"
        ]
    ),

    (
        "EXPERIENCE",
        [
            r"\bexperience\s+&?\s+past\s+performance\b",
            r"\bpast\s+performance\s+certificate\b",
            r"\bsimilar\s+experience\b"
        ]
    ),

    (
        "EMD",
        [
            r"\bemd\s+submission\b",
            r"\bearnest\s+money\s+deposit\b",
            r"\bemd\s+amount\s+required\b"
        ]
    ),

    (
        "DECLARATION",
        [
            r"\bnon[- ]blacklisting\b",
            r"\bnon[- ]debarment\b",
            r"\bdebarment\s+declaration\b",
            r"\bblacklisting\s+declaration\b"
        ]
    )
]


def clean_text(text):
    if not text:
        return ""

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n\s*\n+",
        "\n",
        text
    )

    return text.strip()


def table_text(tables):
    result = []

    for table in tables or []:

        for row in table or []:

            cells = [
                str(cell).strip()
                if cell is not None
                else ""
                for cell in row
            ]

            if any(cells):
                result.append(
                    " | ".join(cells)
                )

    return "\n".join(result)


def page_content(page):

    text = clean_text(
        page.get("text", "")
    )

    tables = table_text(
        page.get("tables", [])
    )

    if tables:
        if text:
            text += "\n\n"

        text += tables

    return text.strip()


def deterministic_category(text):

    normalized = text.lower()

    matches = []

    for category, patterns in HEADING_RULES:

        for pattern in patterns:

            if re.search(
                pattern,
                normalized
            ):

                matches.append(
                    category
                )

                break

    # Priority order is important.
    # DigiLocker must beat UDYAM/PAN/GST mentions.
    priority = [
        "DIGILOCKER",
        "OEM_AUTHORIZATION",
        "STARTUP_NSIC",
        "MII_LOCAL_CONTENT",
        "GST",
        "UDYAM",
        "PAN",
        "CIN",
        "TURNOVER",
        "NET_WORTH",
        "BIS",
        "TECHNICAL",
        "STATUTORY",
        "SUPPORTING_DOCUMENT",
        "EXPERIENCE",
        "EMD",
        "DECLARATION"
    ]

    for category in priority:

        if category in matches:
            return category

    return None


SYSTEM_PROMPT = """
You are a document classification engine for a government procurement
bid-compliance system.

Your job is to classify ONLY the CURRENT PAGE.

The objective is to identify WHAT DOCUMENT THE CURRENT PAGE ACTUALLY IS.

CRITICAL RULE:

Classify the page according to its document purpose, heading, and primary
content.

DO NOT classify a document merely because it mentions another document,
identifier, registration number, certificate, or organization.

Examples:

1. "DigiLocker Document Verification Note"
   mentioning GSTIN, PAN and Udyam
   => DIGILOCKER

2. "OEM Authorisation Certificate"
   mentioning local content
   => OEM_AUTHORIZATION

3. "Startup India & NSIC Registration Status"
   => STARTUP_NSIC

4. Udyam certificate containing the bidder name
   => UDYAM

5. OEM turnover certificate
   => TURNOVER
   because the document is a turnover certificate.

6. BIS licence and technical compliance certificate
   => BIS

Do not use previous or next pages to decide the document type.
Previous/next context may only be used to understand whether the current
page is a continuation of the same document.

Never invent a document.

Never classify based only on an identifier appearing inside another document.

Return JSON only.
"""


def build_prompt(page_number, text):

    return f"""
CURRENT PAGE NUMBER: {page_number}

CURRENT PAGE CONTENT:
--------------------
{text}
--------------------

Choose exactly one category from:

{", ".join(CATEGORIES)}

Return exactly:

{{
  "page": {page_number},
  "category": "ONE_CATEGORY",
  "document_title": "short actual document title",
  "confidence": 0.0,
  "reason": "brief explanation based only on the current page"
}}

Rules:

- category MUST be one of the allowed categories.
- page MUST equal {page_number}.
- document_title must describe the actual document on this page.
- Do not use a title from another page.
- Do not classify from a document merely mentioned on the page.
- If a page is clearly a continuation, classify it according to the document
  being continued.
- If no specific document can be established, use OTHER.
- confidence must be between 0 and 1.
"""


def parse_json(response):

    content = response["message"]["content"].strip()

    # Remove accidental markdown fences.
    content = re.sub(
        r"^```json\s*",
        "",
        content,
        flags=re.IGNORECASE
    )

    content = re.sub(
        r"^```\s*",
        "",
        content
    )

    content = re.sub(
        r"\s*```$",
        "",
        content
    )

    start = content.find("{")
    end = content.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            "No JSON object found."
        )

    return json.loads(
        content[start:end + 1]
    )


def valid_result(result, page_number):

    if not isinstance(result, dict):
        return False

    if result.get("page") != page_number:
        return False

    if result.get("category") not in CATEGORIES:
        return False

    if not isinstance(
        result.get("document_title"),
        str
    ):
        return False

    confidence = result.get(
        "confidence"
    )

    if not isinstance(
        confidence,
        (int, float)
    ):
        return False

    return True


def classify_with_llm(
    page_number,
    text
):

    prompt = build_prompt(
        page_number,
        text
    )

    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0,
            "num_ctx": 8192,
            "num_predict": 500
        }
    )

    result = parse_json(
        response
    )

    if not valid_result(
        result,
        page_number
    ):
        raise ValueError(
            f"Invalid classification for page "
            f"{page_number}: {result}"
        )

    return result


def main():

    with open(
        INPUT,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    bidder_id = data.get(
        "bidder_id"
    )

    bidder_name = data.get(
        "bidder_name"
    )

    classified_pages = []

    for page in data["pages"]:

        page_number = page["page"]

        text = page_content(
            page
        )

        if not text:
            result = {
                "page": page_number,
                "category": "EMPTY",
                "confidence": 1.0,
                "document_title": "",
                "reason": "No usable text was extracted."
            }

        else:

            deterministic = (
                deterministic_category(text)
            )

            if deterministic:

                result = {
                    "page": page_number,
                    "category": deterministic,
                    "confidence": 0.99,
                    "document_title": (
                        text.split("\n")[0][:160]
                    ),
                    "reason": (
                        "High-confidence document heading "
                        "matched deterministic classification rule."
                    ),
                    "classification_method":
                        "deterministic"
                }

            else:

                try:

                    result = classify_with_llm(
                        page_number,
                        text
                    )

                    result[
                        "classification_method"
                    ] = "llm"

                except Exception as e:

                    print(
                        f"Classification failed for page "
                        f"{page_number}: {e}"
                    )

                    result = {
                        "page": page_number,
                        "category": "OTHER",
                        "confidence": 0.0,
                        "document_title": "",
                        "reason": (
                            "LLM classification failed; "
                            "manual review required."
                        ),
                        "classification_method":
                            "fallback"
                    }

        classified_pages.append(
            result
        )

    output = {
        "bidder_id": bidder_id,
        "bidder_name": bidder_name,
        "source_file": data.get(
            "source_file"
        ),
        "total_pages": data.get(
            "total_pages",
            len(classified_pages)
        ),
        "pages": classified_pages
    }

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(
        f"Classification completed → {OUTPUT}"
    )


if __name__ == "__main__":
    main()
