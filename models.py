"""Embedding model + reranker. Each has a neural version and a lightweight fallback,
so the project always runs even without PyTorch or an internet connection."""
import math
import zlib
from . import config
from .text_utils import tokenize, keywords

DIM = 384


class Embedder:
    def __init__(self):
        self.model = None
        self.name = "hash"
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(config.EMBED_MODEL)
            self.name = "minilm"
            print("[models] dense embedder: sentence-transformers ->", config.EMBED_MODEL)
        except Exception as e:
            print("[models] sentence-transformers unavailable, using hashing embedder:", e)

    def _hash_vec(self, text):
        v = [0.0] * DIM
        toks = tokenize(text)
        grams = toks + [a + "_" + b for a, b in zip(toks, toks[1:])]
        for g in grams:
            h = zlib.crc32(g.encode())
            v[h % DIM] += 1.0 if (h >> 16) & 1 else -1.0
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / n for x in v]

    def encode(self, texts):
        if self.model is not None:
            return self.model.encode(texts, normalize_embeddings=True,
                                     show_progress_bar=False).tolist()
        return [self._hash_vec(t) for t in texts]


class Reranker:
    def __init__(self):
        self.model = None
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(config.RERANK_MODEL)
            print("[models] reranker: cross-encoder ->", config.RERANK_MODEL)
        except Exception as e:
            print("[models] cross-encoder unavailable, using lexical reranker:", e)

    def score(self, query, passages):
        if self.model is not None:
            return [float(s) for s in self.model.predict([(query, p) for p in passages])]
        q = set(keywords(query))
        out = []
        for p in passages:
            toks = keywords(p)
            if not toks or not q:
                out.append(0.0)
                continue
            hits = sum(1 for t in toks if t in q)
            coverage = len(q & set(toks)) / len(q)
            out.append(coverage * 2 + hits / math.sqrt(len(toks)))
        return out
