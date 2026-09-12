import json
import numpy as np
from sentence_transformers import SentenceTransformer


QUERY_FILE = "extracted/queries.json"
OUTPUT_FILE = "extracted/query_embeddings.npy"


# -----------------------------
# Load queries
# -----------------------------

with open(QUERY_FILE, "r", encoding="utf-8") as f:
    queries = json.load(f)

print(f"Loaded {len(queries)} queries")


# -----------------------------
# Load embedding model
# -----------------------------

print("Loading embedding model...")

model = SentenceTransformer("all-MiniLM-L6-v2")

print("Embedding model loaded")


# -----------------------------
# Extract query text
# -----------------------------

query_texts = [
    item["query"]
    for item in queries
]


# -----------------------------
# Generate embeddings
# -----------------------------

print("Generating query embeddings...")

embeddings = model.encode(
    query_texts,
    convert_to_numpy=True,
    normalize_embeddings=True,
    show_progress_bar=True
)


# -----------------------------
# Save embeddings
# -----------------------------

np.save(OUTPUT_FILE, embeddings)


# -----------------------------
# Information
# -----------------------------

print("\nQuery embedding complete!")

print(f"Number of queries : {len(queries)}")
print(f"Embedding shape   : {embeddings.shape}")
print(f"Dimensions        : {embeddings.shape[1]}")

print(f"\nSaved to:")
print(OUTPUT_FILE)