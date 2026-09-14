import json
import re
from pathlib import Path

from ollama import chat


INPUT = Path(
    "data/bidder_retrieval.json"
)

OUTPUT = Path(
    "data/bidder_evidence.json"
)

MODEL = "qwen2.5:3b"


IDENTIFIER_PATTERNS = {
    "UDYAM": (r"\bUDYAM-[A-Z]{2}-\d{2}-\d{7}\b", "Udyam Registration Number"),
    "GST": (r"\b\d{2}[A-Z]{5}\d{4}[A-Z]\dZ[A-Z0-9]\b", "GSTIN"),
    "PAN": (r"\b[A-Z]{5}\d{4}[A-Z]\b", "PAN"),
    "BIS": (r"\bBIS-[A-Z0-9-]+\b", "BIS Licence Number"),
}


def deterministic_fallback(result):
    """Recover explicit facts from the retrieved PDF text without inventing values."""
    required_type = result.get("required_document_type")
    candidates = result.get("retrieved_chunks", [])
    preferred = [item for item in candidates if item.get("category") == required_type] or candidates

    if required_type in IDENTIFIER_PATTERNS:
        pattern, field = IDENTIFIER_PATTERNS[required_type]
        for item in preferred:
            match = re.search(pattern, item.get("text", ""), re.IGNORECASE)
            if match:
                return [{"document_id": item.get("document_id"), "document_title": item.get("document_title"), "page": item.get("page"), "field": field, "value": match.group(0).upper(), "unit": "", "evidence_text": match.group(0)}]

    if required_type == "TURNOVER":
        for item in preferred:
            text = item.get("text", "")
            match = re.search(r"average\s+annual(?:\s+(?:bidder|oem))?\s+turnover[^\n\r]{0,80}?INR\s*([\d,]+(?:\.\d+)?)", text, re.IGNORECASE)
            if match:
                value = f"INR {match.group(1)}"
                return [{"document_id": item.get("document_id"), "document_title": item.get("document_title"), "page": item.get("page"), "field": "Average Annual Turnover", "value": value, "unit": "INR", "evidence_text": match.group(0)}]

    if required_type == "EXPERIENCE":
        for item in preferred:
            text = item.get("text", "")
            match = re.search(r"documentary\s+evidence[^\n\r.]*similar\s+supply/work\s+experience", text, re.IGNORECASE)
            if match:
                return [{"document_id": item.get("document_id"), "document_title": item.get("document_title"), "page": item.get("page"), "field": "Similar Experience", "value": match.group(0), "unit": "", "evidence_text": match.group(0)}]

    if required_type == "OEM_AUTHORIZATION":
        for item in preferred:
            text = item.get("text", "")
            match = re.search(r"Authorized\s+Bidder\s+(.+?)(?:\s+Authorization\s+Scope|\r?\nAuthorization\s+Scope)", text, re.IGNORECASE | re.DOTALL)
            if match:
                value = " ".join(match.group(1).split())
                return [{"document_id": item.get("document_id"), "document_title": item.get("document_title"), "page": item.get("page"), "field": "Authorized Bidder", "value": value, "unit": "", "evidence_text": match.group(0)}]

    return []


CATEGORY_INSTRUCTIONS = {

    "Udyam / MSME": """
Look for:
- Udyam registration number
- enterprise name
- enterprise type
- registration status
- certificate identity

Do not decide whether the bidder qualifies as an MSE.
Do not decide purchase preference eligibility.
""",

    "GST": """
Look for:
- GSTIN
- legal name
- registration status
- certificate identity
- GST filing information if explicitly present

Do not decide tax compliance unless explicitly supported.
""",

    "PAN / Income Tax": """
Look for:
- PAN
- name on PAN
- income-tax filing status
- assessment year
- acknowledgement details
""",

    "Make in India / Local Content": """
Look for:
- local content percentage
- place of value addition
- Class-I/Class-II supplier declaration
- local-content declaration
- issuing entity
""",

    "EPFO / ESIC": """
Look for:
- EPFO establishment code
- EPFO status
- ESIC registration number
- ESIC status
- contribution status
""",

    "Startup India": """
Look for:
- Startup India recognition
- DPIIT recognition
- startup status
- recognition number/date if present
""",

    "NSIC": """
Look for:
- NSIC registration
- NSIC certificate
- registration number
- registration status
""",

    "OEM Authorization": """
Look for:
- OEM name
- bidder/dealer name
- authorization relationship
- authorization scope
- product covered
- bid number if present
- date if present
""",

    "DigiLocker / Document Verification": """
Look for:
- DigiLocker reference
- verified identifiers
- matched/mismatched status
- digitally fetched document information
""",

    "Blacklisting / Debarment": """
Look for:
- declaration of non-blacklisting
- debarment status
- suspension status
- banning status
- date/status if explicitly stated
""",

    "BIS / DPIIT": """
Look for:
- BIS certificate
- BIS standard
- certification number
- DPIIT recognition
- other explicit BIS/DPIIT evidence
""",

    "Technical Specifications": """
Look for:
- product model
- dimensions
- capacity
- ratings
- standards
- materials
- technical parameters
- performance specifications
- datasheet information
""",

    "Tender-Specific Eligibility": """
Extract only bidder evidence relevant to the supplied requirement.
Do not attempt to summarize the entire bidder packet.
""",

    "Other Statutory Compliance": """
Extract explicit statutory, regulatory, legal or government compliance
information not better classified under another category.
"""
}


SYSTEM_PROMPT = """
You are the evidence extraction component of a government procurement
compliance system.

Your job is to identify FACTUAL BIDDER EVIDENCE from the retrieved
candidate pages.

You are NOT the compliance decision engine.

CRITICAL RULES:

1. Use ONLY the retrieved bidder evidence supplied to you.
2. Never invent missing values.
3. Never calculate compliance.
4. Never say COMPLIANT or NON_COMPLIANT.
5. Never compare a value against the tender threshold.
6. Never borrow a value from a different document unless the supplied
   candidate explicitly contains it.
7. Preserve the distinction between:
   - bidder
   - OEM
   - manufacturer
   - parent company
   - customer
   - issuing authority
8. Preserve conflicting values rather than resolving them yourself.
9. Every extracted fact MUST have a source page.
10. If no candidate actually answers the requirement, return evidence_found=false.
11. Mentioned identifiers do not automatically prove the document is that
    identifier's certificate.

Return JSON only.
"""


def parse_json(content):

    content = content.strip()

    content = re.sub(
        r"^```json\s*",
        "",
        content,
        flags=re.IGNORECASE
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


def build_prompt(result):

    category = result[
        "category"
    ]

    instructions = CATEGORY_INSTRUCTIONS.get(
        category,
        "Extract only explicit factual evidence relevant to the requirement."
    )

    candidates = []

    for item in result.get(
        "retrieved_chunks",
        []
    ):

        candidates.append({
            "chunk_id": item[
                "chunk_id"
            ],
            "document_id": item[
                "document_id"
            ],
            "document_title": item[
                "document_title"
            ],
            "category": item[
                "category"
            ],
            "page": item[
                "page"
            ],
            "text": item[
                "text"
            ]
        })

    return f"""
REQUIREMENT ID:
{result['requirement_id']}

REQUIREMENT CATEGORY:
{category}

TENDER REQUIREMENT:
{result['requirement']}

EVIDENCE SEARCH INTENT:
{result['evidence_query']}

CATEGORY-SPECIFIC EXTRACTION GUIDANCE:
{instructions}

RETRIEVED BIDDER CANDIDATES:
{json.dumps(candidates, indent=2, ensure_ascii=False)}

Determine whether the retrieved candidates contain actual evidence
relevant to this requirement.

Return exactly:

{{
  "requirement_id": "{result['requirement_id']}",
  "evidence_found": true,
  "evidence": [
    {{
      "document_id": "DOC_XXX",
      "document_title": "...",
      "page": 1,
      "field": "...",
      "value": "...",
      "unit": "...",
      "evidence_text": "exact or near-exact supporting text"
    }}
  ],
  "ambiguities": []
}}

If no candidate provides actual evidence:

{{
  "requirement_id": "{result['requirement_id']}",
  "evidence_found": false,
  "evidence": [],
  "ambiguities": [
    "No retrieved bidder document provides sufficient evidence."
  ]
}}

IMPORTANT:

Do NOT output:
COMPLIANT
NON_COMPLIANT
PARTIALLY_COMPLIANT

Do NOT determine whether a numerical threshold is satisfied.

Only extract the facts.
"""


def validate_output(
    output,
    requirement_id
):

    if not isinstance(
        output,
        dict
    ):
        return False

    if output.get(
        "requirement_id"
    ) != requirement_id:
        return False

    if not isinstance(
        output.get(
            "evidence_found"
        ),
        bool
    ):
        return False

    if not isinstance(
        output.get(
            "evidence"
        ),
        list
    ):
        return False

    return True


def main():

    with open(
        INPUT,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    final_results = []

    for result in data[
        "results"
    ]:

        prompt = build_prompt(
            result
        )

        try:

            response = chat(
                model=MODEL,
                format="json",
                messages=[
                    {
                        "role":
                            "system",
                        "content":
                            SYSTEM_PROMPT
                    },
                    {
                        "role":
                            "user",
                        "content":
                            prompt
                    }
                ],
                options={
                    "temperature": 0,
                    "num_ctx": 12288,
                    "num_predict": 1200
                }
            )

            extracted = parse_json(
                response[
                    "message"
                ][
                    "content"
                ]
            )

            if not validate_output(
                extracted,
                result[
                    "requirement_id"
                ]
            ):

                raise ValueError(
                    "Invalid evidence JSON."
                )

            if not extracted.get("evidence_found"):
                fallback = deterministic_fallback(result)
                if fallback:
                    extracted = {"requirement_id": result["requirement_id"], "evidence_found": True, "evidence": fallback, "ambiguities": []}

        except Exception as e:

            fallback = deterministic_fallback(result)

            extracted = {
                "requirement_id":
                    result[
                        "requirement_id"
                    ],

                "evidence_found":
                    bool(fallback),

                "evidence": fallback,

                "ambiguities": [
                    f"Evidence extraction failed: {e}"
                ] if not fallback else []
            }

        final_results.append(
            extracted
        )

    output = {
        "bidder_id":
            data.get(
                "bidder_id"
            ),

        "bidder_name":
            data.get(
                "bidder_name"
            ),

        "results":
            final_results
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
        f"Saved evidence → {OUTPUT}"
    )


if __name__ == "__main__":
    main()
