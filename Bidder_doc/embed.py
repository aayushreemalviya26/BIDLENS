import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = Path(
    "data/bidder_chunks.json"
)

EMBEDDING_FILE = Path(
    "data/bidder_chunk_embeddings.npy"
)

METADATA_FILE = Path(
    "data/bidder_chunk_metadata.json"
)

MODEL_NAME = "all-MiniLM-L6-v2"


# ============================================================
# BUILD EMBEDDING TEXT
# ============================================================

def build_embedding_text(chunk):

    return f"""
Document title: {chunk.get("document_title", "")}

Document category: {chunk.get("category", "")}

Page: {chunk.get("page", "")}

Evidence:
{chunk.get("text", "")}
""".strip()


# ============================================================
# VALIDATE CHUNK
# ============================================================

def validate_chunk(chunk, index):

    required_fields = [
        "chunk_id",
        "bidder_id",
        "document_id",
        "document_title",
        "category",
        "page",
        "text"
    ]

    missing = [
        field
        for field in required_fields
        if field not in chunk
    ]

    if missing:

        raise ValueError(
            f"Chunk {index} is missing fields: "
            f"{missing}"
        )

    if not chunk["bidder_id"]:

        raise ValueError(
            f"Chunk {index} has empty bidder_id."
        )

    if not chunk["chunk_id"]:

        raise ValueError(
            f"Chunk {index} has empty chunk_id."
        )


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Load chunks
    # --------------------------------------------------------

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Chunk file not found: {INPUT_FILE}"
        )

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    chunks = data.get(
        "chunks",
        []
    )

    print(
        f"Loaded {len(chunks)} bidder chunks."
    )

    if not chunks:

        raise ValueError(
            "No bidder chunks found."
        )

    # --------------------------------------------------------
    # Validate chunks BEFORE loading model
    # --------------------------------------------------------

    print(
        "Validating chunk metadata..."
    )

    for index, chunk in enumerate(
        chunks,
        start=1
    ):

        validate_chunk(
            chunk,
            index
        )

    bidder_ids = {
        chunk["bidder_id"]
        for chunk in chunks
    }

    if len(bidder_ids) != 1:

        raise ValueError(
            "Multiple bidder IDs found in chunks: "
            f"{bidder_ids}"
        )

    bidder_id = next(
        iter(bidder_ids)
    )

    print(
        f"Bidder ID: {bidder_id}"
    )

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
    # Build embedding input
    # --------------------------------------------------------

    embedding_texts = [
        build_embedding_text(chunk)
        for chunk in chunks
    ]

    print(
        "Generating embeddings..."
    )

    embeddings = model.encode(
        embedding_texts,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    # --------------------------------------------------------
    # Validate embedding output
    # --------------------------------------------------------

    if len(embeddings) != len(chunks):

        raise ValueError(
            "Number of embeddings does not match "
            "number of chunks."
        )

    # --------------------------------------------------------
    # Save embeddings
    # --------------------------------------------------------

    np.save(
        EMBEDDING_FILE,
        embeddings
    )

    # --------------------------------------------------------
    # Build metadata
    # --------------------------------------------------------

    metadata = []

    for chunk in chunks:

        metadata.append({

            "chunk_id":
                chunk["chunk_id"],

            "bidder_id":
                chunk["bidder_id"],

            "bidder_name":
                chunk.get(
                    "bidder_name",
                    data.get(
                        "bidder_name",
                        ""
                    )
                ),

            "document_id":
                chunk["document_id"],

            "document_title":
                chunk["document_title"],

            "category":
                chunk["category"],

            "page":
                chunk["page"],

            "page_start":
                chunk.get(
                    "page_start",
                    chunk["page"]
                ),

            "page_end":
                chunk.get(
                    "page_end",
                    chunk["page"]
                ),

            "chunk_index":
                chunk.get(
                    "chunk_index",
                    1
                ),

            "word_count":
                chunk.get(
                    "word_count",
                    len(
                        chunk["text"].split()
                    )
                ),

            "text":
                chunk["text"]
        })

    # --------------------------------------------------------
    # Save metadata
    # --------------------------------------------------------

    with open(
        METADATA_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            metadata,
            f,
            indent=4,
            ensure_ascii=False
        )

    # --------------------------------------------------------
    # Final validation
    # --------------------------------------------------------

    print(
        "\nEmbedding completed successfully."
    )

    print(
        "Embedding shape:",
        embeddings.shape
    )

    print(
        "Number of metadata records:",
        len(metadata)
    )

    print(
        "Bidder ID:",
        bidder_id
    )

    print(
        "\nSaved:"
    )

    print(
        f"  {EMBEDDING_FILE}"
    )

    print(
        f"  {METADATA_FILE}"
    )


if __name__ == "__main__":
    main()