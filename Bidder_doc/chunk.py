import json
import re
from pathlib import Path


PAGES = Path("data/bidder_pages.json")
DOCUMENTS = Path("data/bidder_documents.json")
OUTPUT = Path("data/bidder_chunks.json")


MAX_WORDS = 250
MIN_WORDS = 8


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


def table_to_text(tables):

    rows = []

    for table in tables or []:

        for row in table or []:

            cells = [
                str(cell).strip()
                if cell is not None
                else ""
                for cell in row
            ]

            if any(cells):
                rows.append(
                    " | ".join(cells)
                )

    return "\n".join(rows)


def page_text(page):

    text = clean_text(
        page.get("text", "")
    )

    table_text = table_to_text(
        page.get("tables", [])
    )

    if table_text:

        if text:
            text += "\n\n"

        text += (
            "[TABLE]\n"
            + table_text
        )

    return text.strip()


def split_text(text):

    paragraphs = re.split(
        r"\n+",
        text
    )

    chunks = []
    current = []
    current_words = 0

    for paragraph in paragraphs:

        paragraph = paragraph.strip()

        if not paragraph:
            continue

        words = paragraph.split()

        if len(words) > MAX_WORDS:

            if current:
                chunks.append(
                    " ".join(current)
                )

                current = []
                current_words = 0

            for i in range(
                0,
                len(words),
                MAX_WORDS
            ):

                part = " ".join(
                    words[
                        i:i + MAX_WORDS
                    ]
                )

                if len(
                    part.split()
                ) >= MIN_WORDS:

                    chunks.append(
                        part
                    )

            continue

        if (
            current_words + len(words)
            > MAX_WORDS
        ):

            chunks.append(
                " ".join(current)
            )

            current = []
            current_words = 0

        current.append(
            paragraph
        )

        current_words += len(words)

    if current:

        chunks.append(
            " ".join(current)
        )

    return [
        chunk.strip()
        for chunk in chunks
        if len(
            chunk.split()
        ) >= MIN_WORDS
    ]


def main():

    with open(
        PAGES,
        "r",
        encoding="utf-8"
    ) as f:

        page_data = json.load(f)

    with open(
        DOCUMENTS,
        "r",
        encoding="utf-8"
    ) as f:

        document_data = json.load(f)

    bidder_id = (
        page_data.get("bidder_id")
        or document_data.get("bidder_id")
    )

    bidder_name = (
        page_data.get("bidder_name")
        or document_data.get("bidder_name")
    )

    pages = {
        p["page"]: p
        for p in page_data["pages"]
    }

    page_to_document = {}

    for document in document_data[
        "documents"
    ]:

        for page_number in document[
            "pages"
        ]:

            page_to_document[
                page_number
            ] = document

    chunks = []

    for page_number in sorted(
        pages
    ):

        page = pages[
            page_number
        ]

        document = page_to_document.get(
            page_number
        )

        if not document:
            continue

        text = page_text(
            page
        )

        if not text:
            continue

        pieces = split_text(
            text
        )

        for index, piece in enumerate(
            pieces
        ):

            chunk_id = (
                f"{document['document_id']}"
                f"_P{page_number:03d}"
                f"_C{index + 1:02d}"
            )

            chunks.append({

                # NEVER lose bidder identity.
                "bidder_id": bidder_id,
                "bidder_name": bidder_name,

                "chunk_id": chunk_id,

                "document_id": document[
                    "document_id"
                ],

                "document_title": document[
                    "document_title"
                ],

                "category": document[
                    "category"
                ],

                "page": page_number,

                "page_start": page_number,
                "page_end": page_number,

                "chunk_index": index + 1,

                "text": piece,

                "word_count": len(
                    piece.split()
                )
            })

    output = {
        "bidder_id": bidder_id,
        "bidder_name": bidder_name,
        "total_chunks": len(chunks),
        "chunks": chunks
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
        f"Created {len(chunks)} chunks."
    )

    print(
        f"Saved to {OUTPUT}"
    )


if __name__ == "__main__":
    main()