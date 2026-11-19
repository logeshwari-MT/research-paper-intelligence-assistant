"""Advanced RAG retrieval:
   dense (ChromaDB)  +  sparse (BM25)  ->  Reciprocal Rank Fusion  ->  cross-encoder rerank."""
import chromadb
from rank_bm25 import BM25Okapi
from . import config, db
from .models import Embedder, Reranker
from .text_utils import tokenize

RRF_K = 60


class Retriever:
    def __init__(self):
        self.embedder = Embedder()
        self.reranker = Reranker()
        self.client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
        # collection name includes the embedder so vectors of different sizes never mix
        self.col = self.client.get_or_create_collection(
            name=f"papers_{self.embedder.name}", metadata={"hnsw:space": "cosine"})
        self.rows = []
        self.bm25 = None
        self.rebuild_bm25()

    # ---------- index management ----------
    def rebuild_bm25(self):
        self.rows = db.all_chunks()
        corpus = [tokenize(r["text"]) for r in self.rows]
        self.bm25 = BM25Okapi(corpus) if corpus else None

    def index_chunks(self, paper_id, chunk_rows):
        """chunk_rows: [(chunk_id, page, text)]"""
        texts = [t for _, _, t in chunk_rows]
        for i in range(0, len(texts), 64):                     # batch to keep memory low
            batch = chunk_rows[i:i + 64]
            self.col.add(
                ids=[str(cid) for cid, _, _ in batch],
                embeddings=self.embedder.encode([t for _, _, t in batch]),
                documents=[t for _, _, t in batch],
                metadatas=[{"paper_id": paper_id, "page": p} for _, p, _ in batch])
        self.rebuild_bm25()

    def remove_paper(self, paper_id):
        try:
            self.col.delete(where={"paper_id": paper_id})
        except Exception as e:
            print("[retriever] chroma delete failed:", e)
        self.rebuild_bm25()

    # ---------- search ----------
    def _dense(self, query, paper_ids):
        total = self.col.count()
        if total == 0:
            return []
        where = {"paper_id": {"$in": paper_ids}} if paper_ids else None
        try:
            res = self.col.query(query_embeddings=self.embedder.encode([query]),
                                 n_results=min(config.CANDIDATES, total), where=where)
        except Exception as e:
            print("[retriever] dense query failed:", e)
            return []
        return [int(i) for i in res["ids"][0]]

    def _sparse(self, query, paper_ids):
        if not self.bm25:
            return []
        scores = self.bm25.get_scores(tokenize(query))
        ranked = sorted(range(len(self.rows)), key=lambda i: scores[i], reverse=True)
        out = []
        for i in ranked:
            r = self.rows[i]
            if scores[i] <= 0:
                break
            if paper_ids and r["paper_id"] not in paper_ids:
                continue
            out.append(r["id"])
            if len(out) >= config.CANDIDATES:
                break
        return out

    def search(self, query, paper_ids=None, top_k=config.TOP_K):
        dense = self._dense(query, paper_ids)
        sparse = self._sparse(query, paper_ids)

        fused = {}
        for ranking in (dense, sparse):
            for rank, cid in enumerate(ranking):
                fused[cid] = fused.get(cid, 0.0) + 1.0 / (RRF_K + rank + 1)
        candidates = sorted(fused, key=fused.get, reverse=True)[:config.CANDIDATES]
        if not candidates:
            return []

        by_id = {r["id"]: r for r in self.rows}
        cands = [by_id[c] for c in candidates if c in by_id]
        scores = self.reranker.score(query, [c["text"] for c in cands])
        ranked = sorted(zip(cands, scores), key=lambda x: x[1], reverse=True)[:top_k]
        return [{"chunk_id": c["id"], "paper_id": c["paper_id"], "title": c["title"],
                 "page": c["page"], "text": c["text"], "score": round(float(s), 4),
                 "in_dense": c["id"] in dense, "in_sparse": c["id"] in sparse}
                for c, s in ranked]
