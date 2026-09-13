import json
import re
from pathlib import Path


PAGES = Path("data/bidder_pages.json")
CLASSIFIED = Path("data/bidder_classified.json")
OUTPUT = Path("data/bidder_documents.json")


ISOLATED_CATEGORIES = {
    "EMPTY",
    "GENERAL"
}


def normalize(text):
    if not text:
        return ""

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def title_tokens(title):

    stopwords = {
        "certificate",
        "registration",
        "the",
        "of",
        "and",
        "for",
        "document",
        "status"
    }

    return {
        token
        for token in normalize(title).split()
        if len(token) > 2
        and token not in stopwords
    }


def token_similarity(a, b):

    a_tokens = title_tokens(a)
    b_tokens = title_tokens(b)

    if not a_tokens or not b_tokens:
        return 0.0

    return len(
        a_tokens & b_tokens
    ) / len(
        a_tokens | b_tokens
    )


def is_continuation(page_text):

    text = normalize(
        page_text
    )

    continuation_patterns = [
        r"\bcontinued\b",
        r"\bcontinuation\b",
        r"\bcontinued\s+on\b",
        r"\bcontd\b",
        r"\bpage\s+\d+\s+of\s+\d+\b"
    ]

    return any(
        re.search(
            pattern,
            text
        )
        for pattern in continuation_patterns
    )


def suspicious_classification(
    category,
    title,
    text
):

    text_norm = normalize(text)
    title_norm = normalize(title)

    if category == "OTHER":

        if (
            "oem authorisation" in text_norm
            or "oem authorization" in text_norm
        ):
            return True

        if (
            "startup india" in text_norm
            or "nsic" in text_norm
        ):
            return True

        if "digilocker" in text_norm:
            return True

    return False


def make_document(
    doc_number,
    pages,
    classifications
):

    first = pages[0]
    last = pages[-1]

    category = classifications[
        first
    ]["category"]

    title = classifications[
        first
    ].get(
        "document_title",
        ""
    )

    document = {
        "document_id": (
            f"DOC_{doc_number:03d}"
        ),
        "category": category,
        "document_title": title,
        "page_start": first,
        "page_end": last,
        "pages": pages,
        "page_count": len(pages),
        "confidence": min(
            classifications[p]["confidence"]
            for p in pages
        ),
        "classification_reasons": [
            classifications[p].get(
                "reason",
                ""
            )
            for p in pages
        ],
        "needs_review": any(
            classifications[p].get(
                "needs_review",
                False
            )
            for p in pages
        )
    }

    return document


def main():

    with open(
        PAGES,
        "r",
        encoding="utf-8"
    ) as f:

        page_data = json.load(f)

    with open(
        CLASSIFIED,
        "r",
        encoding="utf-8"
    ) as f:

        classified_data = json.load(f)

    bidder_id = (
        page_data.get("bidder_id")
        or classified_data.get("bidder_id")
    )

    bidder_name = (
        page_data.get("bidder_name")
        or classified_data.get("bidder_name")
    )

    pages_by_number = {
        p["page"]: p
        for p in page_data["pages"]
    }

    classifications = {
        p["page"]: p
        for p in classified_data["pages"]
    }

    documents = []

    current_pages = []
    current_category = None
    current_title = None

    def flush():

        nonlocal current_pages

        if not current_pages:
            return

        document = make_document(
            len(documents) + 1,
            current_pages,
            classifications
        )

        documents.append(
            document
        )

        current_pages = []

    for page_number in sorted(
        pages_by_number
    ):

        classification = (
            classifications[page_number]
        )

        category = classification[
            "category"
        ]

        title = classification.get(
            "document_title",
            ""
        )

        text = pages_by_number[
            page_number
        ].get(
            "text",
            ""
        )

        suspicious = suspicious_classification(
            category,
            title,
            text
        )

        if suspicious:

            classification[
                "needs_review"
            ] = True

            classification[
                "reason"
            ] += (
                " Classification conflict detected "
                "between category/title and page content."
            )

        if category in ISOLATED_CATEGORIES:

            flush()

            current_pages = [
                page_number
            ]

            flush()

            current_category = None
            current_title = None

            continue

        if not current_pages:

            current_pages = [
                page_number
            ]

            current_category = category
            current_title = title

            continue

        previous_page = current_pages[-1]

        # Different categories normally mean
        # different documents.
        if category != current_category:

            flush()

            current_pages = [
                page_number
            ]

            current_category = category
            current_title = title

            continue

        similarity = token_similarity(
            current_title,
            title
        )

        continuation = is_continuation(
            text
        )

        # Same category + strong title similarity
        # OR explicit continuation.
        if (
            similarity >= 0.35
            or continuation
        ):

            current_pages.append(
                page_number
            )

        else:

            flush()

            current_pages = [
                page_number
            ]

            current_category = category
            current_title = title

    flush()

    output = {
        "bidder_id": bidder_id,
        "bidder_name": bidder_name,
        "source_file": page_data.get(
            "source_file"
        ),
        "total_pages": page_data.get(
            "total_pages"
        ),
        "total_documents": len(
            documents
        ),
        "documents": documents
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
        f"Created {len(documents)} documents."
    )

    print(
        f"Saved to {OUTPUT}"
    )


if __name__ == "__main__":
    main()