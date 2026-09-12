import json
import re
from pathlib import Path
from statistics import mean


# =========================================================
# FILES
# =========================================================

INPUT_FILE = Path("extracted/cleaned_tender_pages.json")
OUTPUT_FILE = Path("extracted/tender_chunks.json")


# =========================================================
# SETTINGS
# =========================================================

# A normal clause stays intact.
# Only very large clauses are split.
MAX_WORDS = 600

# Used only when a single clause is larger than MAX_WORDS.
OVERLAP_WORDS = 50


# =========================================================
# REGEX PATTERNS
# =========================================================

# Genuine numbered clause:
#
# 1. Eligibility
# 2. Scope
# 3. Technical Requirements
# 2.1 Experience
# 2.1.1 Minimum Experience
#
# IMPORTANT:
# We require "." after the number.
#
# This prevents things such as:
# 2017
# 16.09.2020
# 120 (Days)
# from being interpreted as clauses.
STRICT_CLAUSE_PATTERN = re.compile(
    r"^\s*(\d+(?:\.\d+)*)\s*\.\s+(.+)$"
)


# Sub-items:
#
# (a) ...
# (b) ...
# (i) ...
# (ii) ...
# a) ...
# b) ...
# 1) ...
SUBITEM_PATTERN = re.compile(
    r"^\s*(?:\([a-zA-Z0-9]+\)|[a-zA-Z0-9]\))\s+.+"
)


# Page-number artifacts:
#
# 1 / 15
# 2 / 15
# Page 1 of 15
PAGE_NUMBER_PATTERN = re.compile(
    r"^\s*(?:page\s*)?\d+\s*(?:/|of)\s*\d+\s*$",
    re.IGNORECASE
)


# =========================================================
# METADATA KEYWORDS
# =========================================================

# These are common GeM/bid metadata fields.
# They should NOT become artificial clauses.
METADATA_KEYWORDS = [
    "bid number",
    "bid end date",
    "bid opening date",
    "validity",
    "ministry/state name",
    "ministry name",
    "department name",
    "organisation name",
    "organization name",
    "office name",
    "estimated bid value",
    "bid quantity",
    "item category",
    "delivery period",
    "place of delivery",
    "bid validity",
    "oem average turnover",
    "minimum average annual turnover",
    "years of past experience",
    "experience with similar products",
]


# =========================================================
# HEADING KEYWORDS
# =========================================================

HEADING_KEYWORDS = [
    "eligibility",
    "qualification",
    "technical specification",
    "scope of supply",
    "scope of work",
    "terms and conditions",
    "general conditions",
    "special conditions",
    "commercial conditions",
    "bid submission",
    "evaluation",
    "payment terms",
    "warranty",
    "performance security",
    "emd",
    "tender conditions",
    "technical requirements",
]


# =========================================================
# BASIC CHECKS
# =========================================================

def is_page_artifact(line):
    """
    Detect obvious page numbering such as:

        1 / 15
        2 / 15
        Page 3 of 15
    """

    return bool(
        PAGE_NUMBER_PATTERN.match(line.strip())
    )


def looks_like_date(line):
    """
    Detect dates such as:

        16.09.2020
        22-08-2026
        22/08/2026
        2026-08-22
    """

    line = line.strip()

    # DD.MM.YYYY
    if re.match(
        r"^\d{1,2}\.\d{1,2}\.\d{2,4}",
        line
    ):
        return True

    # DD-MM-YYYY
    if re.match(
        r"^\d{1,2}-\d{1,2}-\d{2,4}",
        line
    ):
        return True

    # DD/MM/YYYY
    if re.match(
        r"^\d{1,2}/\d{1,2}/\d{2,4}",
        line
    ):
        return True

    # YYYY-MM-DD
    if re.match(
        r"^\d{4}-\d{1,2}-\d{1,2}",
        line
    ):
        return True

    return False


def looks_like_metadata(line):
    """
    Detect GeM/bid metadata.
    """

    lower = line.lower().strip()

    # Keyword-based detection
    for keyword in METADATA_KEYWORDS:

        if keyword in lower:
            return True

    # -----------------------------------------------------
    # Numeric + unit metadata
    #
    # Examples:
    # 120 (Days) Validity
    # 102 Lakh(s) OEM Average Turnover
    # -----------------------------------------------------

    if re.match(
        r"^\s*\d+(?:\.\d+)?\s*"
        r"\(\s*(?:days?|months?|years?|lakh|lakhs|crore|crores)\s*\)",
        line,
        re.IGNORECASE
    ):
        return True

    # -----------------------------------------------------
    # Other numeric metadata
    # -----------------------------------------------------

    metadata_words = [
        "turnover",
        "value",
        "quantity",
        "days",
        "months",
        "years",
        "validity",
        "period",
        "experience",
        "amount",
        "percentage",
    ]

    if re.match(
        r"^\s*(?:₹|rs\.?|inr)?\s*"
        r"\d[\d,]*(?:\.\d+)?\s*"
        r"(?:lakh|lakhs|crore|crores)?\b",
        line,
        re.IGNORECASE
    ):

        if any(
            word in lower
            for word in metadata_words
        ):
            return True

    return False


# =========================================================
# CLAUSE DETECTION
# =========================================================

def get_clause_id(line):
    """
    Return a clause ID only when the line strongly resembles
    a real tender clause.

    Accepted:

        1. Eligibility
        2. Scope
        3. Technical Specifications
        2.1 Experience
        2.1.1 Minimum Experience

    Rejected:

        2017 ...
        16.09.2020 ...
        120 (Days) ...
        102 Lakh(s) ...
        1 / 15
    """

    line = line.strip()

    if not line:
        return None

    # Page number
    if is_page_artifact(line):
        return None

    # Date
    if looks_like_date(line):
        return None

    # Metadata
    if looks_like_metadata(line):
        return None

    # -----------------------------------------------------
    # Require strict numbered clause format
    # -----------------------------------------------------

    match = STRICT_CLAUSE_PATTERN.match(line)

    if not match:
        return None

    clause_number = match.group(1)
    content = match.group(2).strip()

    if not content:
        return None

    # -----------------------------------------------------
    # Reject obvious numeric values
    # -----------------------------------------------------

    if re.match(
        r"^\d+(?:\.\d+)?\s*"
        r"(?:days?|months?|years?|lakh|lakhs|crore|crores|%)\b",
        content,
        re.IGNORECASE
    ):
        return None

    # -----------------------------------------------------
    # Reject lines whose content is basically numbers
    # -----------------------------------------------------

    if re.fullmatch(
        r"[\d\s./:%()\-]+",
        content
    ):
        return None

    return clause_number


def is_main_clause(line):
    return get_clause_id(line) is not None


# =========================================================
# HEADING DETECTION
# =========================================================

def is_heading(line):

    line = line.strip()

    if not line:
        return False

    lower = line.lower()

    # Known tender section heading
    if len(line.split()) <= 15:

        for keyword in HEADING_KEYWORDS:

            if keyword in lower:
                return True

    # ALL CAPS heading
    if len(line.split()) <= 15:

        if line.upper() == line:

            if any(
                character.isalpha()
                for character in line
            ):
                return True

    return False


# =========================================================
# SPLIT LARGE CLAUSE
# =========================================================

def split_large_clause(text):

    words = text.split()

    # Normal clause
    if len(words) <= MAX_WORDS:
        return [text]

    result = []

    start = 0

    while start < len(words):

        end = min(
            start + MAX_WORDS,
            len(words)
        )

        part = words[start:end]

        result.append(
            " ".join(part)
        )

        if end >= len(words):
            break

        start = end - OVERLAP_WORDS

    return result


# =========================================================
# PROCESS ONE PAGE
# =========================================================

def process_page(page):

    page_number = page["page"]

    text = page.get(
        "text",
        ""
    )

    lines = text.splitlines()

    page_chunks = []

    current_clause_id = None
    current_lines = []

    section_heading = None

    # -----------------------------------------------------
    # Finish current clause
    # -----------------------------------------------------

    def flush_clause():

        nonlocal current_clause_id
        nonlocal current_lines
        nonlocal section_heading

        if not current_lines:
            return

        content = "\n".join(
            line.strip()
            for line in current_lines
            if line.strip()
        ).strip()

        if not content:

            current_lines = []
            current_clause_id = None

            return

        # Add section context if available
        if section_heading:

            content = (
                f"Section: {section_heading}\n"
                f"{content}"
            )

        # Split only exceptionally large clauses
        parts = split_large_clause(content)

        for part in parts:

            page_chunks.append({
                "page": page_number,
                "chunk_type": "clause",
                "clause_id": current_clause_id,
                "section": section_heading,
                "text": part
            })

        current_lines = []
        current_clause_id = None

    # =====================================================
    # PROCESS TEXT
    # =====================================================

    for raw_line in lines:

        line = raw_line.strip()

        if not line:
            continue

        # Ignore page numbers
        if is_page_artifact(line):
            continue

        # -------------------------------------------------
        # New actual clause
        # -------------------------------------------------

        clause_id = get_clause_id(line)

        if clause_id is not None:

            # Finish previous clause
            flush_clause()

            current_clause_id = clause_id

            current_lines = [line]

            continue

        # -------------------------------------------------
        # Heading
        # -------------------------------------------------

        if is_heading(line):

            # If we're already inside a clause,
            # keep the heading as part of that clause.
            if current_clause_id is not None:

                current_lines.append(line)

            else:

                section_heading = line

            continue

        # -------------------------------------------------
        # Normal text
        # -------------------------------------------------

        if current_clause_id is not None:

            current_lines.append(line)

        else:

            # Unnumbered content.
            #
            # We preserve it rather than throwing it away.
            current_lines.append(line)

    # Finish last clause
    flush_clause()

    # =====================================================
    # TABLES
    # =====================================================

    tables = page.get(
        "tables",
        []
    )

    for table_index, table in enumerate(tables):

        if not table:
            continue

        rows = []

        for row in table:

            if not row:
                continue

            cells = []

            for cell in row:

                if cell is None:
                    cells.append("")

                else:
                    cells.append(
                        str(cell).strip()
                    )

            rows.append(
                " | ".join(cells)
            )

        if not rows:
            continue

        table_text = "\n".join(
            rows
        ).strip()

        if not table_text:
            continue

        page_chunks.append({
            "page": page_number,
            "chunk_type": "table",
            "clause_id": None,
            "section": section_heading,
            "table_id": (
                f"T_{page_number:03d}_"
                f"{table_index + 1:02d}"
            ),
            "text": table_text
        })

    return page_chunks


# =========================================================
# REMOVE DUPLICATES
# =========================================================

def remove_duplicates(chunks):

    seen = set()

    unique_chunks = []

    for chunk in chunks:

        key = (
            chunk["page"],
            chunk["chunk_type"],
            chunk.get("clause_id"),
            chunk.get("table_id"),
            chunk.get("text", "").strip()
        )

        if key in seen:
            continue

        seen.add(key)

        unique_chunks.append(chunk)

    return unique_chunks


# =========================================================
# ASSIGN CHUNK IDs
# =========================================================

def assign_chunk_ids(chunks):

    for index, chunk in enumerate(
        chunks,
        start=1
    ):

        chunk["chunk_id"] = (
            f"CH_{index:04d}"
        )

    return chunks


# =========================================================
# STATISTICS
# =========================================================

def print_statistics(chunks):

    clause_chunks = [
        c for c in chunks
        if c["chunk_type"] == "clause"
    ]

    table_chunks = [
        c for c in chunks
        if c["chunk_type"] == "table"
    ]

    word_counts = [
        len(c["text"].split())
        for c in chunks
        if c["text"].strip()
    ]

    print("\n========================================")
    print("CHUNKING COMPLETED")
    print("========================================")

    print(
        f"Total chunks       : {len(chunks)}"
    )

    print(
        f"Clause chunks      : {len(clause_chunks)}"
    )

    print(
        f"Table chunks       : {len(table_chunks)}"
    )

    if word_counts:

        print(
            f"Average words      : "
            f"{mean(word_counts):.1f}"
        )

        print(
            f"Maximum words      : "
            f"{max(word_counts)}"
        )

        print(
            f"Minimum words      : "
            f"{min(word_counts)}"
        )

    # -----------------------------------------------------
    # Clause IDs
    # -----------------------------------------------------

    clause_ids = [
        c["clause_id"]
        for c in clause_chunks
        if c.get("clause_id") is not None
    ]

    unique_clause_ids = list(
        dict.fromkeys(clause_ids)
    )

    print(
        f"Detected clauses   : "
        f"{len(unique_clause_ids)}"
    )


# =========================================================
# SHOW SAMPLE
# =========================================================

def print_sample(chunks):

    print("\n========================================")
    print("FIRST 15 CHUNKS")
    print("========================================")

    for chunk in chunks[:15]:

        preview = (
            chunk["text"]
            .replace("\n", " ")
        )

        if len(preview) > 220:

            preview = (
                preview[:220]
                + "..."
            )

        print(
            f"\n{chunk['chunk_id']} | "
            f"Page {chunk['page']} | "
            f"{chunk['chunk_type']} | "
            f"Clause {chunk.get('clause_id')}"
        )

        print(preview)


# =========================================================
# MAIN
# =========================================================

def main():

    # -----------------------------------------------------
    # Check input
    # -----------------------------------------------------

    if not INPUT_FILE.exists():

        print(
            "ERROR: Input file not found:"
        )

        print(
            INPUT_FILE
        )

        return

    # -----------------------------------------------------
    # Load cleaned pages
    # -----------------------------------------------------

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        pages = json.load(f)

    # -----------------------------------------------------
    # Create chunks
    # -----------------------------------------------------

    all_chunks = []

    for page in pages:

        page_chunks = process_page(page)

        all_chunks.extend(
            page_chunks
        )

    # -----------------------------------------------------
    # Remove duplicates
    # -----------------------------------------------------

    all_chunks = remove_duplicates(
        all_chunks
    )

    # -----------------------------------------------------
    # Assign IDs
    # -----------------------------------------------------

    all_chunks = assign_chunk_ids(
        all_chunks
    )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            all_chunks,
            f,
            indent=4,
            ensure_ascii=False
        )

    # -----------------------------------------------------
    # Print results
    # -----------------------------------------------------

    print_statistics(
        all_chunks
    )

    print(
        "\nSaved to:"
    )

    print(
        OUTPUT_FILE
    )

    print_sample(
        all_chunks
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()