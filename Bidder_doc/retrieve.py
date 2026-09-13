import json
import re
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIG
# ============================================================

CHUNKS_FILE = Path(
    "data/bidder_chunks.json"
)

EMBEDDING_FILE = Path(
    "data/bidder_chunk_embeddings.npy"
)

METADATA_FILE = Path(
    "data/bidder_chunk_metadata.json"
)

REQUIREMENTS_CANDIDATES = [
    Path("data/extracted_requirements.json"),
    Path("data/requirements.json"),
    Path("data/requirements_raw.json"),
    Path("data/queries.json"),
    Path("data/queries.jsonl"),
]

OUTPUT_FILE = Path(
    "data/bidder_retrieval.json"
)

MODEL_NAME = "all-MiniLM-L6-v2"


# ============================================================
# RETRIEVAL PARAMETERS
# ============================================================

# Number of candidates considered after initial semantic search.
CANDIDATE_K = 15

# Maximum number finally returned for evidence extraction.
FINAL_K = 5

# Minimum semantic similarity required before a candidate
# can be considered relevant.
MIN_SEMANTIC_SCORE = 0.30

# Minimum combined score required to accept evidence.
MIN_FINAL_SCORE = 0.28


# ============================================================
# CATEGORY → EXPECTED BIDDER DOCUMENT TYPES
# ============================================================
#
# These are deliberately based on the bidder-side evidence
# categories produced by classify.py.
#
# "expected"  = strongest evidence
# "secondary" = supporting evidence
# "negative"  = documents that should generally be penalized
#
# Retrieval does NOT decide compliance.
# It only finds likely evidence.
# ============================================================

CATEGORY_MAP = {

    "Udyam / MSME": {
        "expected": {
            "UDYAM"
        },
        "secondary": {
            "DIGILOCKER"
        },
        "negative": {
            "EMD",
            "EXPERIENCE",
            "GST",
            "PAN",
            "TURNOVER"
        }
    },

    "GST": {
        "expected": {
            "GST"
        },
        "secondary": {
            "DIGILOCKER"
        },
        "negative": {
            "EMD",
            "EXPERIENCE",
            "TURNOVER",
            "UDYAM"
        }
    },

    "PAN / Income Tax": {
        "expected": {
            "PAN"
        },
        "secondary": {
            "DIGILOCKER"
        },
        "negative": {
            "EMD",
            "EXPERIENCE",
            "UDYAM",
            "GST"
        }
    },

    "Make in India / Local Content": {
        "expected": {
            "MII_LOCAL_CONTENT"
        },
        "secondary": {
            "DECLARATION"
        },
        "negative": {
            "EMD",
            "GST",
            "PAN",
            "UDYAM"
        }
    },

    "EPFO / ESIC": {
        "expected": {
            "STATUTORY"
        },
        "secondary": set(),
        "negative": {
            "GST",
            "UDYAM",
            "PAN",
            "EMD",
            "EXPERIENCE",
            "TURNOVER"
        }
    },

    "Startup India": {
        "expected": {
            "STARTUP_NSIC"
        },
        "secondary": set(),
        "negative": {
            "EMD",
            "GST",
            "EXPERIENCE",
            "TURNOVER"
        }
    },

    "NSIC": {
        "expected": {
            "STARTUP_NSIC"
        },
        "secondary": set(),
        "negative": {
            "EMD",
            "GST",
            "EXPERIENCE",
            "TURNOVER"
        }
    },

    "OEM Authorization": {
        "expected": {
            "OEM_AUTHORIZATION"
        },
        "secondary": set(),
        "negative": {
            "EMD",
            "GST",
            "UDYAM",
            "PAN",
            "EXPERIENCE",
            "TURNOVER"
        }
    },

    "DigiLocker / Document Verification": {
        "expected": {
            "DIGILOCKER"
        },
        "secondary": set(),
        "negative": {
            "EMD",
            "EXPERIENCE",
            "TURNOVER",
            "GST"
        }
    },

    "Blacklisting / Debarment": {
        "expected": {
            "DECLARATION"
        },
        "secondary": set(),
        "negative": {
            "EMD",
            "GST",
            "UDYAM",
            "TURNOVER"
        }
    },

    "BIS / DPIIT": {
        "expected": {
            "TECHNICAL",
            "STARTUP_NSIC"
        },
        "secondary": {
            "STATUTORY"
        },
        "negative": {
            "EMD",
            "TURNOVER",
            "EXPERIENCE"
        }
    },

    "Technical Specifications": {
        "expected": {
            "TECHNICAL"
        },
        "secondary": set(),
        "negative": {
            "EMD",
            "EXPERIENCE",
            "TURNOVER",
            "GST",
            "PAN",
            "UDYAM",
            "DECLARATION"
        }
    },

    "Tender-Specific Eligibility": {
        "expected": {
            "CIN",
            "UDYAM",
            "GST",
            "PAN",
            "STATUTORY",
            "EXPERIENCE",
            "TURNOVER",
            "OEM_AUTHORIZATION",
            "MII_LOCAL_CONTENT",
            "STARTUP_NSIC",
            "DIGILOCKER",
            "EMD",
            "DECLARATION"
        },
        "secondary": {
            "TECHNICAL",
            "SUPPORTING_DOCUMENT",
            "OTHER"
        },
        "negative": set()
    },

    "Other Statutory Compliance": {
        "expected": {
            "STATUTORY",
            "DECLARATION"
        },
        "secondary": set(),
        "negative": {
            "EMD",
            "TURNOVER",
            "EXPERIENCE",
            "GST",
            "UDYAM",
            "PAN"
        }
    }
}


# ============================================================
# EVIDENCE-ORIENTED SEARCH QUERIES
# ============================================================
#
# These are intentionally NOT written as:
#
# "Does the tender require..."
#
# They describe the bidder evidence we actually want to retrieve.
# ============================================================

EVIDENCE_QUERIES = {

    "Udyam / MSME":
        """
        bidder Udyam MSME registration certificate,
        Udyam registration number, enterprise name,
        registration status
        """,

    "GST":
        """
        bidder GST registration certificate,
        GSTIN, legal name, GST registration status
        """,

    "PAN / Income Tax":
        """
        bidder PAN card, PAN number, income tax,
        income-tax filing or tax compliance evidence
        """,

    "Make in India / Local Content":
        """
        bidder Make in India declaration,
        local content percentage, local value addition,
        Class-I local supplier, Class-II local supplier
        """,

    "EPFO / ESIC":
        """
        bidder EPFO registration, ESIC registration,
        establishment code, labour statutory compliance
        """,

    "Startup India":
        """
        bidder Startup India recognition,
        DPIIT startup recognition, startup registration,
        recognition status
        """,

    "NSIC":
        """
        bidder NSIC registration, NSIC certificate,
        NSIC registration status
        """,

    "OEM Authorization":
        """
        OEM authorisation certificate,
        manufacturer authorization, authorized dealer,
        bidder authorized by OEM, product authorization
        """,

    "DigiLocker / Document Verification":
        """
        DigiLocker document verification,
        digital document verification,
        verified bidder documents, matched identifiers
        """,

    "Blacklisting / Debarment":
        """
        bidder non-blacklisting declaration,
        non-debarment declaration, debarment status,
        suspension, banning or blacklisting status
        """,

    "BIS / DPIIT":
        """
        bidder BIS certificate, BIS certification,
        BIS standard, DPIIT recognition,
        BIS or DPIIT compliance evidence
        """,

    "Technical Specifications":
        """
        bidder technical specification,
        product datasheet, technical compliance,
        model, dimensions, capacity, ratings,
        standards, performance parameters
        """,

    "Tender-Specific Eligibility":
        """
        bidder eligibility and qualification evidence
        relevant to the specific tender requirement
        """,

    "Other Statutory Compliance":
        """
        bidder statutory, regulatory, legal or
        government compliance evidence
        """
}


# ============================================================
# NORMALIZATION
# ============================================================

def normalize(text):
    """
    Normalize text for lexical/entity matching.

    This is NOT used to replace the original evidence text.
    """

    if not text:
        return ""

    text = str(text).lower()

    text = re.sub(
        r"[^a-z0-9%./-]+",
        " ",
        text
    )

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


def tokens(text):
    return set(
        normalize(text).split()
    )


# ============================================================
# LEXICAL MATCHING
# ============================================================

def lexical_overlap(query, text):

    query_tokens = tokens(query)
    text_tokens = tokens(text)

    if not query_tokens or not text_tokens:
        return 0.0

    return len(
        query_tokens & text_tokens
    ) / len(query_tokens)


def title_overlap(query, title):

    return lexical_overlap(
        query,
        title
    )


# ============================================================
# ENTITY DETECTION
# ============================================================
#
# This prevents semantic similarity alone from being trusted.
#
# Example:
#
# "NSIC" query should prefer a page containing NSIC.
#
# "OEM Authorization" should prefer OEM + authorization.
# ============================================================

ENTITY_PATTERNS = {

    "udyam": [
        r"\budyam\b",
        r"\bmsme\b"
    ],

    "gst": [
        r"\bgst\b",
        r"\bgstin\b"
    ],

    "pan": [
        r"\bpan\b",
        r"\bincome\s+tax\b"
    ],

    "cin": [
        r"\bcin\b",
        r"\bcertificate\s+of\s+incorporation\b"
    ],

    "oem": [
        r"\boem\b",
        r"\bmanufacturer\b"
    ],

    "authorization": [
        r"\bauthori[sz]ation\b",
        r"\bauthori[sz]ed\s+dealer\b"
    ],

    "local_content": [
        r"\blocal\s+content\b",
        r"\blocal\s+value\s+addition\b",
        r"\bmake\s+in\s+india\b"
    ],

    "startup": [
        r"\bstartup\s+india\b",
        r"\bstartup\b",
        r"\bdpiit\b"
    ],

    "nsic": [
        r"\bnsic\b"
    ],

    "digilocker": [
        r"\bdigilocker\b",
        r"\bdigital\s+locker\b"
    ],

    "blacklisting": [
        r"\bblacklist",
        r"\bblack-listed\b"
    ],

    "debarment": [
        r"\bdebar",
        r"\bbanning\b",
        r"\bsuspension\b"
    ],

    "epfo": [
        r"\bepfo\b"
    ],

    "esic": [
        r"\besic\b"
    ],

    "turnover": [
        r"\bturnover\b"
    ],

    "experience": [
        r"\bexperience\b",
        r"\bpast\s+performance\b"
    ],

    "technical": [
        r"\btechnical\b",
        r"\bspecification\b",
        r"\bdatasheet\b",
        r"\bmodel\b",
        r"\bcapacity\b",
        r"\bdimension"
    ]
}


def detect_entities(text):

    normalized = normalize(text)

    found = set()

    for entity, patterns in ENTITY_PATTERNS.items():

        for pattern in patterns:

            if re.search(
                pattern,
                normalized
            ):

                found.add(entity)
                break

    return found


def entity_score(query, text):

    query_entities = detect_entities(
        query
    )

    text_entities = detect_entities(
        text
    )

    if not query_entities:
        return 0.0

    return len(
        query_entities & text_entities
    ) / len(
        query_entities
    )


# ============================================================
# CATEGORY CONFIGURATION
# ============================================================

def category_config(category):

    return CATEGORY_MAP.get(
        category,
        {
            "expected": set(),
            "secondary": set(),
            "negative": set()
        }
    )


# ============================================================
# LOAD REQUIREMENTS
# ============================================================
#
# Supports:
#
# 1. JSON array
# 2. JSON object containing "requirements"
# 3. JSON object containing "queries"
# 4. Single JSON requirement/query
# 5. Real JSONL
#
# This fixes the exact error you encountered.
# ============================================================

def load_requirement_file():

    for path in REQUIREMENTS_CANDIDATES:

        if not path.exists():
            continue

        print(
            f"Loading requirements from: {path}"
        )

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            content = f.read().strip()

        if not content:
            continue

        # ----------------------------------------------------
        # First: try the entire file as normal JSON.
        # ----------------------------------------------------

        try:

            data = json.loads(
                content
            )

            if isinstance(
                data,
                list
            ):

                print(
                    f"Loaded {len(data)} "
                    "requirements/queries."
                )

                return data

            if isinstance(
                data,
                dict
            ):

                if isinstance(
                    data.get("requirements"),
                    list
                ):

                    records = data[
                        "requirements"
                    ]

                    print(
                        f"Loaded {len(records)} "
                        "requirements."
                    )

                    return records

                if isinstance(
                    data.get("queries"),
                    list
                ):

                    records = data[
                        "queries"
                    ]

                    print(
                        f"Loaded {len(records)} "
                        "queries."
                    )

                    return records

                if (
                    "requirement" in data
                    or "query" in data
                    or "requirement_id" in data
                    or "query_id" in data
                ):

                    print(
                        "Loaded 1 requirement/query."
                    )

                    return [data]

        except json.JSONDecodeError:
            pass

        # ----------------------------------------------------
        # Second: try as real JSONL.
        # ----------------------------------------------------

        records = []

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            for line_number, line in enumerate(
                f,
                start=1
            ):

                line = line.strip()

                if not line:
                    continue

                try:

                    record = json.loads(
                        line
                    )

                except json.JSONDecodeError as e:

                    raise ValueError(
                        f"Invalid JSONL in {path} "
                        f"at line {line_number}: {e}"
                    ) from e

                if not isinstance(
                    record,
                    dict
                ):

                    raise ValueError(
                        f"Expected JSON object at "
                        f"line {line_number} in {path}."
                    )

                records.append(
                    record
                )

        if records:

            print(
                f"Loaded {len(records)} "
                "JSONL requirements/queries."
            )

            return records

    raise FileNotFoundError(
        "No valid requirement/query file found.\n"
        "Checked:\n"
        + "\n".join(
            f"  - {path}"
            for path in REQUIREMENTS_CANDIDATES
        )
    )


# ============================================================
# REQUIREMENT NORMALIZATION
# ============================================================

def build_requirement_text(item):

    parts = []

    if item.get("requirement"):
        parts.append(
            f"Requirement: {item['requirement']}"
        )

    if item.get("category"):
        parts.append(
            f"Category: {item['category']}"
        )

    if item.get("requirement_type"):
        parts.append(
            f"Requirement type: "
            f"{item['requirement_type']}"
        )

    if item.get("operator"):
        parts.append(
            f"Operator: {item['operator']}"
        )

    if item.get("required_value") is not None:
        parts.append(
            f"Required value: "
            f"{item['required_value']}"
        )

    if item.get("unit"):
        parts.append(
            f"Unit: {item['unit']}"
        )

    if item.get("clause"):
        parts.append(
            f"Clause: {item['clause']}"
        )

    return "\n".join(parts)


def normalize_requirement(
    item,
    index
):

    requirement_id = (
        item.get("requirement_id")
        or item.get("query_id")
        or f"REQ_{index:03d}"
    )

    category = (
        item.get("category")
        or "Other Statutory Compliance"
    )

    original_requirement = (
        item.get("requirement")
        or item.get("query")
        or ""
    )

    # --------------------------------------------------------
    # Evidence search query
    # --------------------------------------------------------
    #
    # If Part 1 has produced a real requirement,
    # preserve it and append the evidence intent.
    #
    # If using the current Q01-Q14 file, use the
    # category-specific evidence query.
    # --------------------------------------------------------

    category_query = (
        EVIDENCE_QUERIES.get(
            category,
            ""
        )
    )

    if category_query:

        evidence_query = (
            f"{original_requirement}\n"
            f"Evidence to find:\n"
            f"{category_query}"
        )

    else:

        evidence_query = (
            original_requirement
        )

    return {

        "requirement_id":
            requirement_id,

        "category":
            category,

        "requirement":
            original_requirement,

        "evidence_query":
            evidence_query,

        "operator":
            item.get("operator"),

        "required_value":
            item.get("required_value"),

        "unit":
            item.get("unit"),

        "clause":
            item.get("clause")
    }


# ============================================================
# CANDIDATE SCORING
# ============================================================

def score_candidate(
    requirement,
    similarity,
    metadata
):

    category = requirement[
        "category"
    ]

    config = category_config(
        category
    )

    chunk_category = (
        metadata.get(
            "category",
            "OTHER"
        )
    )

    text = metadata.get(
        "text",
        ""
    )

    title = metadata.get(
        "document_title",
        ""
    )

    query = requirement[
        "evidence_query"
    ]

    # --------------------------------------------------------
    # Individual signals
    # --------------------------------------------------------

    semantic = float(
        similarity
    )

    lexical = lexical_overlap(
        query,
        text
    )

    title_score = title_overlap(
        query,
        title
    )

    entities = entity_score(
        query,
        text
    )

    # --------------------------------------------------------
    # Category signal
    # --------------------------------------------------------

    if chunk_category in config[
        "expected"
    ]:

        category_score = 1.0

    elif chunk_category in config[
        "secondary"
    ]:

        category_score = 0.5

    elif chunk_category in config[
        "negative"
    ]:

        category_score = -1.0

    else:

        category_score = 0.0

    # --------------------------------------------------------
    # Combined score
    # --------------------------------------------------------
    #
    # Semantic similarity remains the largest signal.
    #
    # Metadata does not replace semantic search.
    # It corrects obvious semantic false positives.
    # --------------------------------------------------------

    final_score = (

        semantic * 0.55

        + lexical * 0.15

        + title_score * 0.10

        + entities * 0.10

        + category_score * 0.10
    )

    return {

        "semantic_similarity":
            round(semantic, 4),

        "lexical_score":
            round(lexical, 4),

        "title_score":
            round(title_score, 4),

        "entity_score":
            round(entities, 4),

        "category_score":
            round(category_score, 4),

        "final_score":
            round(
                float(final_score),
                4
            )
    }


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Load chunks
    # --------------------------------------------------------

    if not CHUNKS_FILE.exists():

        raise FileNotFoundError(
            f"Missing chunk file: {CHUNKS_FILE}"
        )

    with open(
        CHUNKS_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        chunk_data = json.load(f)

    chunks = chunk_data.get(
        "chunks",
        []
    )

    if not chunks:

        raise ValueError(
            "No bidder chunks found."
        )

    print(
        f"Loaded {len(chunks)} bidder chunks."
    )

    # --------------------------------------------------------
    # Load embeddings
    # --------------------------------------------------------

    if not EMBEDDING_FILE.exists():

        raise FileNotFoundError(
            f"Missing embeddings: "
            f"{EMBEDDING_FILE}"
        )

    embeddings = np.load(
        EMBEDDING_FILE
    )

    # --------------------------------------------------------
    # Load metadata
    # --------------------------------------------------------

    if not METADATA_FILE.exists():

        raise FileNotFoundError(
            f"Missing metadata: "
            f"{METADATA_FILE}"
        )

    with open(
        METADATA_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        metadata = json.load(f)

    # --------------------------------------------------------
    # Integrity checks
    # --------------------------------------------------------

    if len(chunks) != len(
        embeddings
    ):

        raise ValueError(
            "Chunk count does not match "
            "embedding count.\n"
            f"Chunks: {len(chunks)}\n"
            f"Embeddings: {len(embeddings)}"
        )

    if len(metadata) != len(
        embeddings
    ):

        raise ValueError(
            "Metadata count does not match "
            "embedding count.\n"
            f"Metadata: {len(metadata)}\n"
            f"Embeddings: {len(embeddings)}"
        )

    # --------------------------------------------------------
    # Check bidder IDs
    # --------------------------------------------------------

    bidder_ids = {
        item.get("bidder_id")
        for item in metadata
    }

    if None in bidder_ids:

        raise ValueError(
            "At least one chunk has "
            "bidder_id=None.\n"
            "Fix chunk.py before retrieval."
        )

    if len(bidder_ids) != 1:

        raise ValueError(
            "Multiple bidder IDs found: "
            f"{bidder_ids}"
        )

    bidder_id = next(
        iter(bidder_ids)
    )

    bidder_name = (
        chunk_data.get(
            "bidder_name",
            ""
        )
    )

    print(
        f"Bidder ID: {bidder_id}"
    )

    print(
        f"Bidder name: {bidder_name}"
    )

    # --------------------------------------------------------
    # Load requirements
    # --------------------------------------------------------

    requirements_raw = (
        load_requirement_file()
    )

    requirements = [
        normalize_requirement(
            item,
            index
        )
        for index, item in enumerate(
            requirements_raw,
            start=1
        )
    ]

    # --------------------------------------------------------
    # Load embedding model
    # --------------------------------------------------------

    print(
        "Loading embedding model..."
    )

    model = SentenceTransformer(
        MODEL_NAME
    )

    # --------------------------------------------------------
    # Retrieval
    # --------------------------------------------------------

    results = []

    for requirement in requirements:

        requirement_id = (
            requirement[
                "requirement_id"
            ]
        )

        category = (
            requirement[
                "category"
            ]
        )

        query = (
            requirement[
                "evidence_query"
            ]
        )

        print(
            f"\nRetrieving: "
            f"{requirement_id} | {category}"
        )

        # ----------------------------------------------------
        # Query embedding
        # ----------------------------------------------------

        query_embedding = model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        )[0]

        similarities = np.dot(
            embeddings,
            query_embedding
        )

        # ----------------------------------------------------
        # Category configuration
        # ----------------------------------------------------

        config = category_config(
            category
        )

        expected_categories = config[
            "expected"
        ]

        secondary_categories = config[
            "secondary"
        ]

        # ----------------------------------------------------
        # Stage 1:
        # semantic candidate generation
        # ----------------------------------------------------
        #
        # We do NOT hard-filter to one category.
        #
        # Why?
        #
        # Some evidence may legitimately be in a supporting
        # document, e.g. DigiLocker verification supporting
        # Udyam/GST/PAN.
        #
        # Instead, we retrieve semantically first and then
        # use category metadata during reranking.
        # ----------------------------------------------------

        all_indices = list(
            range(len(metadata))
        )

        all_indices.sort(
            key=lambda i:
                similarities[i],
            reverse=True
        )

        candidate_indices = all_indices[
            :CANDIDATE_K
        ]

        # ----------------------------------------------------
        # Stage 2:
        # deterministic reranking
        # ----------------------------------------------------

        scored_candidates = []

        for index in candidate_indices:

            score = score_candidate(
                requirement,
                similarities[index],
                metadata[index]
            )

            candidate = {

                "chunk_id":
                    metadata[index].get(
                        "chunk_id"
                    ),

                "bidder_id":
                    metadata[index].get(
                        "bidder_id"
                    ),

                "bidder_name":
                    metadata[index].get(
                        "bidder_name",
                        bidder_name
                    ),

                "document_id":
                    metadata[index].get(
                        "document_id"
                    ),

                "document_title":
                    metadata[index].get(
                        "document_title"
                    ),

                "category":
                    metadata[index].get(
                        "category"
                    ),

                "page":
                    metadata[index].get(
                        "page"
                    ),

                "page_start":
                    metadata[index].get(
                        "page_start",
                        metadata[index].get(
                            "page"
                        )
                    ),

                "page_end":
                    metadata[index].get(
                        "page_end",
                        metadata[index].get(
                            "page"
                        )
                    ),

                "text":
                    metadata[index].get(
                        "text",
                        ""
                    ),

                "score":
                    score
            }

            scored_candidates.append(
                candidate
            )

        scored_candidates.sort(
            key=lambda item:
                item["score"]["final_score"],
            reverse=True
        )

        # ----------------------------------------------------
        # Stage 3:
        # relevance threshold
        # ----------------------------------------------------
        #
        # This is essential.
        #
        # The system is allowed to say:
        #
        #     NO EVIDENCE
        #
        # rather than returning an unrelated document.
        # ----------------------------------------------------

        accepted = []

        for candidate in scored_candidates:

            semantic_score = (
                candidate[
                    "score"
                ][
                    "semantic_similarity"
                ]
            )

            final_score = (
                candidate[
                    "score"
                ][
                    "final_score"
                ]
            )

            category_score = (
                candidate[
                    "score"
                ][
                    "category_score"
                ]
            )

            # ------------------------------------------------
            # Strong protection against obvious wrong-category
            # results.
            #
            # If we KNOW a category is expected and this is a
            # clearly negative category, don't accept it merely
            # because semantic similarity was high.
            # ------------------------------------------------

            if (
                expected_categories
                and category_score < 0
            ):

                continue

            if semantic_score < MIN_SEMANTIC_SCORE:
                continue

            if final_score < MIN_FINAL_SCORE:
                continue

            accepted.append(
                candidate
            )

        # ----------------------------------------------------
        # Limit final results.
        # ----------------------------------------------------

        accepted = accepted[
            :FINAL_K
        ]

        evidence_found = bool(
            accepted
        )

        # ----------------------------------------------------
        # Result object
        # ----------------------------------------------------

        result = {

            "requirement_id":
                requirement_id,

            "category":
                category,

            "requirement":
                requirement[
                    "requirement"
                ],

            "evidence_query":
                query,

            "operator":
                requirement[
                    "operator"
                ],

            "required_value":
                requirement[
                    "required_value"
                ],

            "unit":
                requirement[
                    "unit"
                ],

            "clause":
                requirement[
                    "clause"
                ],

            "evidence_found":
                evidence_found,

            "retrieved_count":
                len(accepted),

            "retrieved_chunks":
                accepted
        }

        if not evidence_found:

            result[
                "reason"
            ] = (
                "No bidder chunk passed the "
                "retrieval relevance threshold."
            )

        results.append(
            result
        )

        # ----------------------------------------------------
        # Console summary
        # ----------------------------------------------------

        if accepted:

            best = accepted[0]

            print(
                f"  BEST → "
                f"{best['document_id']} | "
                f"{best['category']} | "
                f"page {best['page']} | "
                f"score "
                f"{best['score']['final_score']}"
            )

        else:

            print(
                "  BEST → NO EVIDENCE"
            )

    # ========================================================
    # SAVE
    # ========================================================

    output = {

        "bidder_id":
            bidder_id,

        "bidder_name":
            bidder_name,

        "total_requirements":
            len(results),

        "results":
            results
    }

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
            output,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(
        "\n========================================"
    )

    print(
        "Retrieval completed successfully."
    )

    print(
        f"Requirements processed: {len(results)}"
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )

    print(
        "========================================"
    )


if __name__ == "__main__":
    main()