import json
import numpy as np
from sentence_transformers import SentenceTransformer


# -----------------------------
# Paths
# -----------------------------

INPUT_FILE = "extracted/tender_chunks.json"
EMBEDDING_FILE = "extracted/chunk_embeddings.npy"
METADATA_FILE = "extracted/chunk_metadata.json"


# -----------------------------
# Load chunks
# -----------------------------

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    chunks = json.load(f)

print(f"Loaded {len(chunks)} chunks")


# -----------------------------
# Load embedding model
# -----------------------------

print("Loading embedding model...")

model = SentenceTransformer("all-MiniLM-L6-v2")

print("Embedding model loaded")


# -----------------------------
# Extract text
# -----------------------------

texts = []

for chunk in chunks:
    texts.append(chunk["text"])


# -----------------------------
# Generate embeddings
# -----------------------------

print("Generating embeddings...")

embeddings = model.encode(
    texts,
    show_progress_bar=True,
    convert_to_numpy=True,
    normalize_embeddings=True
)


# -----------------------------
# Save embeddings
# -----------------------------

np.save(EMBEDDING_FILE, embeddings)

# # Human-readable copy of embeddings
# EMBEDDING_JSON_FILE = "extracted/chunk_embeddings.json"

# embedding_data = []

# for chunk, embedding in zip(chunks, embeddings):
#     embedding_data.append({
#         "chunk_id": chunk["chunk_id"],
#         "page": chunk["page"],
#         "chunk_type": chunk["chunk_type"],
#         "embedding": embedding.tolist()
#     })

# with open(EMBEDDING_JSON_FILE, "w", encoding="utf-8") as f:
#     json.dump(embedding_data, f, ensure_ascii=False, indent=2)


# -----------------------------
# Save metadata separately
# -----------------------------

metadata = []

for chunk in chunks:
    metadata.append({
        "chunk_id": chunk["chunk_id"],
        "page": chunk["page"],
        "chunk_type": chunk["chunk_type"],
        "text": chunk["text"]
    })


with open(METADATA_FILE, "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)


# -----------------------------
# Information
# -----------------------------

print("\nEmbedding complete!")

print(f"Number of chunks : {len(chunks)}")
print(f"Embedding shape   : {embeddings.shape}")
print(f"Embedding size    : {embeddings.shape[1]} dimensions")

print(f"\nSaved:")
print(f"  {EMBEDDING_FILE}")
# print(f"  {EMBEDDING_JSON_FILE}")
print(f"  {METADATA_FILE}")