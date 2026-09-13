import json
import re
import numpy as np


# ============================================================
# FILE PATHS
# ============================================================

CHUNK_EMBEDDINGS_PATH = "extracted/chunk_embeddings.npy"
CHUNK_METADATA_PATH = "extracted/chunk_metadata.json"
QUERY_EMBEDDINGS_PATH = "extracted/query_embeddings.npy"

OUTPUT_PATH = "extracted/retrieved_chunks.json"


# ============================================================
# SETTINGS
# ============================================================

CANDIDATE_K = 15
FINAL_K = 5


# ============================================================
# CATEGORY-SPECIFIC TERMS
# ============================================================

CATEGORY_TERMS = {

    "Udyam / MSME": [
        "udyam",
        "msme",
        "micro enterprise",
        "small enterprise",
        "medium enterprise",
        "micro, small and medium",
        "msme registration",
        "udyam registration"
    ],

    "GST": [
        "gst",
        "gstin",
        "goods and services tax",
        "gst registration",
        "gst certificate",
        "gst return"
    ],

    "PAN / Income Tax": [
        "pan",
        "pan card",
        "permanent account number",
        "income tax",
        "income-tax",
        "income tax return",
        "itr"
    ],

    "Make in India / Local Content": [
        "make in india",
        "local content",
        "local sourcing",
        "domestic value addition",
        "class i local supplier",
        "class ii local supplier",
        "class-i local supplier",
        "class-ii local supplier"
    ],

    "EPFO / ESIC": [
        "epfo",
        "esic",
        "employee provident fund",
        "provident fund",
        "employees state insurance",
        "social security"
    ],

    "Startup India": [
        "startup india",
        "startup",
        "dpiit startup",
        "startup recognition",
        "startup registration"
    ],

    "NSIC": [
        "nsic",
        "nsic registration",
        "nsic certificate",
        "national small industries corporation"
    ],

    "OEM Authorization": [
        "oem",
        "original equipment manufacturer",
        "manufacturer authorization",
        "oem authorization",
        "authorization letter",
        "manufacturer certificate"
    ],

    "DigiLocker / Document Verification": [
        "digilocker",
        "digi locker",
        "digital locker",
        "digital verification",
        "digitally verified",
        "online verification",
        "document verification"
    ],

    "Blacklisting / Debarment": [
        "blacklisted",
        "blacklist",
        "debarred",
        "debarment",
        "suspended",
        "suspension",
        "banned",
        "ban",
        "non-performance"
    ],

    "BIS / DPIIT": [
        "bis",
        "bis certificate",
        "bureau of indian standards",
        "dpiit",
        "dpiit recognition",
        "dpiit certificate"
    ],

    "Technical Specifications": [
        "technical specification",
        "technical specifications",
        "specification",
        "product specification",
        "technical requirement",
        "performance requirement",
        "capacity",
        "dimension",
        "material",
        "configuration",
        "processor",
        "memory",
        "storage",
        "operating system"
    ],

    "Tender-Specific Eligibility": [
        "eligibility",
        "eligible",
        "qualification",
        "experience",
        "turnover",
        "financial",
        "technical qualification",
        "bidder qualification",
        "documentary evidence",
        "participation"
    ],

    "Other Statutory Compliance": [
        "statutory",
        "regulatory",
        "legal compliance",
        "registration",
        "certificate",
        "certification",
        "declaration",
        "compliance",
        "government registration"
    ]
}


# ============================================================
# GENERIC REQUIREMENT TERMS
# ============================================================

ACTION_TERMS = [
    "shall",
    "must",
    "required",
    "requirement",
    "requirements",
    "submit",
    "submitted",
    "provide",
    "provided",
    "attach",
    "attached",
    "upload",
    "produce",
    "furnish",
    "declare",
    "declaration",
    "mandatory",
    "eligible",
    "eligibility",
    "certificate",
    "certification",
    "registration",
    "proof",
    "documentary evidence"
]


# ============================================================
# GENERIC / LOW-VALUE TERMS
# ============================================================

GENERIC_TERMS = [
    "tender fee",
    "bid fee",
    "emd",
    "earnest money deposit",
    "fdr",
    "dd",
    "bank guarantee",
    "payment",
    "delivery",
    "completion certificate",
    "technical data sheet",
    "data sheet",
    "general conditions",
    "general terms",
    "tender document"
]


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_text(text):

    text = str(text).lower()

    text = text.replace("–", "-")
    text = text.replace("—", "-")
    text = text.replace("’", "'")

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# FIND TERM POSITIONS
# ============================================================

def find_term_positions(text, terms):

    positions = []

    for term in terms:

        term = normalize_text(term)

        if not term:
            continue

        start = 0

        while True:

            position = text.find(
                term,
                start
            )

            if position == -1:
                break

            positions.append(position)

            start = position + len(term)

    return positions


# ============================================================
# CATEGORY SIGNAL
# ============================================================

def category_score(text, category):

    text = normalize_text(text)

    terms = CATEGORY_TERMS.get(
        category,
        []
    )

    matched_terms = []

    for term in terms:

        term = normalize_text(term)

        if term in text:
            matched_terms.append(term)

    matched_terms = list(
        set(matched_terms)
    )

    if len(matched_terms) == 0:
        return 0.0

    elif len(matched_terms) == 1:
        return 0.7

    elif len(matched_terms) == 2:
        return 0.9

    else:
        return 1.0


# ============================================================
# EXACT CATEGORY PHRASE
# ============================================================
#
# IMPORTANT CHANGE:
#
# Earlier this only considered multi-word phrases.
#
# Now ALL category terms can receive exact-match credit.
#
# Examples:
#
# GST       -> exact = 1.0
# GSTIN     -> exact = 1.0
# PAN       -> exact = 1.0
# Udyam     -> exact = 1.0
# NSIC      -> exact = 1.0
# EPFO      -> exact = 1.0
# ESIC      -> exact = 1.0
# BIS       -> exact = 1.0
# OEM       -> exact = 1.0
#
# ============================================================

def exact_phrase_score(text, category):

    text = normalize_text(text)

    terms = CATEGORY_TERMS.get(
        category,
        []
    )

    for term in terms:

        term = normalize_text(term)

        if not term:
            continue

        # Word-boundary matching prevents
        # "pan" from matching unrelated words
        # such as "payment".
        pattern = r"\b" + re.escape(term) + r"\b"

        if re.search(pattern, text):

            return 1.0

    return 0.0


# ============================================================
# REQUIREMENT SIGNAL
# ============================================================

def requirement_score(text):

    text = normalize_text(text)

    count = 0

    for term in ACTION_TERMS:

        if term in text:
            count += 1

    if count == 0:
        return 0.0

    elif count == 1:
        return 0.4

    elif count == 2:
        return 0.7

    else:
        return 1.0


# ============================================================
# REQUIREMENT NEAR CATEGORY
# ============================================================

def requirement_near_category(
    text,
    category
):

    text = normalize_text(text)

    category_terms = CATEGORY_TERMS.get(
        category,
        []
    )

    category_positions = find_term_positions(
        text,
        category_terms
    )

    if not category_positions:
        return 0.0

    best_score = 0.0

    for position in category_positions:

        start = max(
            0,
            position - 150
        )

        end = min(
            len(text),
            position + 250
        )

        context = text[start:end]

        action_count = 0

        for action in ACTION_TERMS:

            if action in context:
                action_count += 1

        if action_count >= 2:

            score = 1.0

        elif action_count == 1:

            score = 0.7

        else:

            score = 0.2

        best_score = max(
            best_score,
            score
        )

    return best_score


# ============================================================
# GENERIC SIGNAL
# ============================================================

def generic_signal(text):

    text = normalize_text(text)

    count = 0

    for term in GENERIC_TERMS:

        if normalize_text(term) in text:
            count += 1

    if count == 0:

        return 0.0

    elif count == 1:

        return 0.5

    else:

        return 1.0


# ============================================================
# CHUNK TYPE SIGNAL
# ============================================================

def type_score(chunk):

    chunk_type = str(
        chunk.get(
            "chunk_type",
            ""
        )
    ).lower()

    if chunk_type == "table":

        return 1.0

    if chunk_type == "paragraph":

        return 0.5

    return 0.2


# ============================================================
# RERANK SCORE
# ============================================================

def calculate_rerank_score(
    similarity,
    category_signal,
    requirement_signal,
    exact_signal,
    type_signal,
    generic_signal,
    nearby_requirement_signal
):

    # --------------------------------------------------------
    # NO CATEGORY EVIDENCE
    # --------------------------------------------------------
    #
    # Do NOT reward generic requirement language.
    #
    # Example:
    #
    # Q07 NSIC
    #
    # Chunk:
    # "BIS certificate must be submitted"
    #
    # NSIC not present -> category = 0
    #
    # Therefore generic "must submit certificate"
    # should NOT make this chunk look highly relevant.
    #
    # --------------------------------------------------------

    if (
        category_signal == 0
        and exact_signal == 0
    ):

        score = (
            similarity * 0.72
            + type_signal * 0.03
            - generic_signal * 0.25
        )

        return score


    # --------------------------------------------------------
    # CATEGORY EVIDENCE EXISTS
    # --------------------------------------------------------

    score = (
        similarity * 0.50
        + category_signal * 0.15
        + requirement_signal * 0.05
        + exact_signal * 0.25
        + nearby_requirement_signal * 0.20
        + type_signal * 0.03
        - generic_signal * 0.20
    )

    return score


# ============================================================
# LOAD EMBEDDINGS
# ============================================================

print("=" * 60)
print("LOADING EMBEDDINGS AND METADATA")
print("=" * 60)

chunk_embeddings = np.load(
    CHUNK_EMBEDDINGS_PATH
)

query_embeddings = np.load(
    QUERY_EMBEDDINGS_PATH
)

with open(
    CHUNK_METADATA_PATH,
    "r",
    encoding="utf-8"
) as f:

    chunk_metadata = json.load(f)


print(
    "Chunk embeddings:",
    chunk_embeddings.shape
)

print(
    "Query embeddings:",
    query_embeddings.shape
)

print(
    "Chunks:",
    len(chunk_metadata)
)


# ============================================================
# NORMALIZE EMBEDDINGS
# ============================================================

chunk_norms = np.linalg.norm(
    chunk_embeddings,
    axis=1,
    keepdims=True
)

chunk_embeddings = (
    chunk_embeddings /
    np.maximum(
        chunk_norms,
        1e-12
    )
)


query_norms = np.linalg.norm(
    query_embeddings,
    axis=1,
    keepdims=True
)

query_embeddings = (
    query_embeddings /
    np.maximum(
        query_norms,
        1e-12
    )
)


# ============================================================
# FIXED QUERY SET
# ============================================================

QUERIES = [

    {
        "query_id": "Q01",
        "category": "Udyam / MSME",
        "query": "Does the tender require Udyam or MSME registration, certification, status, or any proof of Micro, Small and Medium Enterprise registration?"
    },

    {
        "query_id": "Q02",
        "category": "GST",
        "query": "Does the tender require GST registration, GST certification, GST return filing, or any other GST-related compliance or documentation?"
    },

    {
        "query_id": "Q03",
        "category": "PAN / Income Tax",
        "query": "Does the tender require PAN, Income Tax registration, Income Tax compliance, tax returns, or any other income-tax related document or verification?"
    },

    {
        "query_id": "Q04",
        "category": "Make in India / Local Content",
        "query": "Does the tender specify Make in India, local content, local sourcing, domestic value addition, Class I or Class II local supplier requirements, or other local-content conditions?"
    },

    {
        "query_id": "Q05",
        "category": "EPFO / ESIC",
        "query": "Does the tender require EPFO or ESIC registration, contribution compliance, certificates, returns, or any other employee social-security compliance?"
    },

    {
        "query_id": "Q06",
        "category": "Startup India",
        "query": "Does the tender mention Startup India registration, recognition, startup eligibility, exemptions, benefits, or any startup-specific requirement?"
    },

    {
        "query_id": "Q07",
        "category": "NSIC",
        "query": "Does the tender require NSIC registration, NSIC certification, NSIC eligibility, exemptions, or any other NSIC-related requirement?"
    },

    {
        "query_id": "Q08",
        "category": "OEM Authorization",
        "query": "Does the tender require OEM authorization, manufacturer authorization, an OEM certificate, authorization letter, or proof that the bidder is authorized by the original equipment manufacturer?"
    },

    {
        "query_id": "Q09",
        "category": "DigiLocker / Document Verification",
        "query": "Does the tender require DigiLocker documents, digitally verified documents, online document verification, or submission of documents through an official digital repository?"
    },

    {
        "query_id": "Q10",
        "category": "Blacklisting / Debarment",
        "query": "Does the tender contain requirements related to bidder blacklisting, debarment, suspension, banning, non-performance, or declaration that the bidder is not blacklisted or debarred?"
    },

    {
        "query_id": "Q11",
        "category": "BIS / DPIIT",
        "query": "Does the tender require BIS certification, BIS standards, DPIIT recognition, DPIIT certification, or compliance with any BIS or DPIIT requirement?"
    },

    {
        "query_id": "Q12",
        "category": "Technical Specifications",
        "query": "What technical specifications, product characteristics, performance requirements, standards, features, dimensions, capacities, materials, or other technical requirements does the tender specify for the product?"
    },

    {
        "query_id": "Q13",
        "category": "Tender-Specific Eligibility",
        "query": "What bidder eligibility, qualification, experience, financial, technical, commercial, documentary, or other tender-specific requirements are explicitly required for participation?"
    },

    {
        "query_id": "Q14",
        "category": "Other Statutory Compliance",
        "query": "Does the tender mention any other statutory, regulatory, legal, government registration, certification, declaration, or compliance requirement that is not covered by the other categories?"
    }
]


# ============================================================
# RETRIEVAL
# ============================================================

all_results = []


for query_index, query_info in enumerate(
    QUERIES
):

    query_id = query_info["query_id"]

    category = query_info["category"]

    query_text = query_info["query"]

    print("\n")
    print("=" * 60)
    print(
        query_id,
        "-",
        category
    )
    print("=" * 60)


    # --------------------------------------------------------
    # STEP 1: QUERY VECTOR
    # --------------------------------------------------------

    query_vector = query_embeddings[
        query_index
    ]


    # --------------------------------------------------------
    # STEP 2: COSINE SIMILARITY
    # --------------------------------------------------------

    similarities = np.dot(
        chunk_embeddings,
        query_vector
    )


    # --------------------------------------------------------
    # STEP 3: CANDIDATE GENERATION
    # --------------------------------------------------------

    candidate_indices = np.argsort(
        similarities
    )[::-1][:CANDIDATE_K]


    candidates = []


    # --------------------------------------------------------
    # STEP 4: RERANK
    # --------------------------------------------------------

    for index in candidate_indices:

        chunk = chunk_metadata[index]

        text = chunk.get(
            "text",
            ""
        )

        similarity = float(
            similarities[index]
        )


        # Category evidence
        cat_signal = category_score(
            text,
            category
        )


        # Generic requirement language
        req_signal = requirement_score(
            text
        )


        # Exact category term
        exact_signal = exact_phrase_score(
            text,
            category
        )


        # Requirement close to category term
        nearby_signal = requirement_near_category(
            text,
            category
        )


        # Generic / low-value content
        gen_signal = generic_signal(
            text
        )


        # Paragraph/table/etc.
        typ_signal = type_score(
            chunk
        )


        # Final reranking score
        final_score = calculate_rerank_score(
            similarity=similarity,
            category_signal=cat_signal,
            requirement_signal=req_signal,
            exact_signal=exact_signal,
            type_signal=typ_signal,
            generic_signal=gen_signal,
            nearby_requirement_signal=nearby_signal
        )


        candidates.append({

            "chunk_id": chunk.get(
                "chunk_id"
            ),

            "page": chunk.get(
                "page"
            ),

            "chunk_type": chunk.get(
                "chunk_type"
            ),

            "clause_id": chunk.get(
                "clause_id"
            ),

            "section": chunk.get(
                "section"
            ),

            "similarity": round(
                similarity,
                4
            ),

            "category_score": round(
                cat_signal,
                4
            ),

            "requirement_score": round(
                req_signal,
                4
            ),

            "exact_phrase_score": round(
                exact_signal,
                4
            ),

            "nearby_requirement_score": round(
                nearby_signal,
                4
            ),

            "generic_score": round(
                gen_signal,
                4
            ),

            "type_score": round(
                typ_signal,
                4
            ),

            "final_score": round(
                final_score,
                4
            ),

            "text": text
        })


    # --------------------------------------------------------
    # STEP 5: SORT BY RERANK SCORE
    # --------------------------------------------------------

    candidates.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )


    # --------------------------------------------------------
    # STEP 6: TOP 5
    # --------------------------------------------------------

    final_results = candidates[
        :FINAL_K
    ]


    # --------------------------------------------------------
    # PRINT
    # --------------------------------------------------------

    for rank, result in enumerate(
        final_results,
        start=1
    ):

        print(
            f"\nRank {rank}: "
            f"{result['chunk_id']}"
        )

        print(
            f"Page: "
            f"{result['page']}"
        )

        print(
            f"Similarity: "
            f"{result['similarity']}"
        )

        print(
            f"Category: "
            f"{result['category_score']}"
        )

        print(
            f"Requirement: "
            f"{result['requirement_score']}"
        )

        print(
            f"Exact: "
            f"{result['exact_phrase_score']}"
        )

        print(
            f"Nearby: "
            f"{result['nearby_requirement_score']}"
        )

        print(
            f"Generic: "
            f"{result['generic_score']}"
        )

        print(
            f"Final score: "
            f"{result['final_score']}"
        )

        print(
            "Text:",
            result["text"][:300]
            .replace("\n", " ")
        )


    # --------------------------------------------------------
    # STORE RESULT
    # --------------------------------------------------------

    all_results.append({

        "query_id": query_id,

        "category": category,

        "query": query_text,

        "results": final_results
    })


# ============================================================
# SAVE RESULTS
# ============================================================

with open(
    OUTPUT_PATH,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        all_results,
        f,
        indent=4,
        ensure_ascii=False
    )


# ============================================================
# DONE
# ============================================================

print("\n")
print("=" * 60)
print("RETRIEVAL COMPLETED")
print("=" * 60)

print(
    "Candidate K:",
    CANDIDATE_K
)

print(
    "Final K:",
    FINAL_K
)

print(
    "Saved to:",
    OUTPUT_PATH
)