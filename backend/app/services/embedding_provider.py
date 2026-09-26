"""Explicit lightweight lexical vectors for the free judge host; MiniLM locally.

Not neural embeddings: fixed hashed unigram/bigram counts preserve the pipeline's
retrieval interface while keeping its category reranking and compliance rules.
"""
import hashlib
import os
import re

import numpy as np


class SentenceTransformer:
    def __init__(self, model, **kwargs):
        self.local = None
        mode = os.getenv("BIDLENS_RETRIEVAL", "minilm")
        if mode == "minilm":
            from sentence_transformers import SentenceTransformer as MiniLM
            self.local = MiniLM(model, **kwargs)
        elif mode != "lexical":
            raise ValueError("BIDLENS_RETRIEVAL must be minilm or lexical")

    def encode(self, texts, **kwargs):
        if self.local is not None:
            return self.local.encode(texts, **kwargs)
        single = isinstance(texts, str)
        rows = []
        for text in [texts] if single else texts:
            words = re.findall(r"[a-z0-9]+", text.casefold())
            terms = words + [a + " " + b for a, b in zip(words, words[1:])]
            vector = np.zeros(2048, dtype=np.float32)
            for term in terms:
                bucket = int.from_bytes(hashlib.sha256(term.encode()).digest()[:4], "little") % 2048
                vector[bucket] += 1
            vector = np.log1p(vector)
            vector /= max(float(np.linalg.norm(vector)), 1e-8)
            rows.append(vector)
        return rows[0] if single else np.asarray(rows)
