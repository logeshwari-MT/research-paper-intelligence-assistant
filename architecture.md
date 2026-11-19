# Architecture

```
PDF --> pypdf (text per page) --> chunker (180 words, 30 overlap, keeps page number)
    --> SQLite (chunks)  +  embedder --> ChromaDB (vectors)
                         +  BM25 index (rebuilt in memory from SQLite)

Question --> dense search (Chroma, top 20)  \
         --> keyword search (BM25, top 20)   > Reciprocal Rank Fusion --> top 20
                                            /
         --> cross-encoder rerank --> top 5 passages --> LLM prompt (numbered context)
         --> answer with [1][2] citations --> mapped back to paper title + page
```

## Why each part exists
- Chunking with overlap: keeps sentences that straddle a boundary retrievable.
- Dense embeddings: match meaning ("accuracy" vs "performance") even when words differ.
- BM25: matches exact terms (model names, dataset names, acronyms) that embeddings blur.
- RRF: merges two rankings that have different score scales, using rank only: score = sum 1/(60 + rank).
- Cross-encoder rerank: reads question and passage together, so it is more accurate than
  vector similarity but too slow for the whole corpus, hence only on the top 20.
- Grounded prompt: the LLM may only use numbered passages and must cite them, which reduces hallucination.
- Fallbacks: hashing embedder and lexical reranker keep the system running without PyTorch.

## Data
- papers(id, title, filename, pages, n_chunks)
- chunks(id, paper_id, page, text)
- messages(id, question, answer, sources json, mode)
- Chroma collection `papers_<embedder>` with metadata {paper_id, page}
