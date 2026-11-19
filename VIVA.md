# Viva preparation

## 30-second pitch
Researchers waste time reading many papers to find one fact. This system lets you upload PDFs and ask
questions in natural language. It finds the most relevant passages using hybrid search (semantic + keyword),
reranks them, and gives them to an LLM, which writes an answer with citations to paper and page.

## Key terms
- RAG: retrieve relevant text first, then generate an answer from it, so the LLM is grounded in your documents.
- Embedding: a vector that represents the meaning of text; similar meanings give nearby vectors.
- ChromaDB: the vector database storing chunk embeddings.
- BM25: a keyword ranking formula based on term frequency and rarity.
- RRF (Reciprocal Rank Fusion): combines ranked lists using only ranks.
- Cross-encoder: a model scoring a (question, passage) pair jointly.
- Hallucination: the LLM inventing facts; reduced by grounding and citations.

## Likely questions and answers
1. Why RAG instead of fine-tuning? Papers change, fine-tuning is costly and cannot show sources. RAG updates by uploading a file and gives citations.
2. Why hybrid search? Embeddings capture meaning but can miss exact terms; BM25 does the reverse. Together recall is higher.
3. Why rerank? Fast retrieval gets candidates; the slower cross-encoder picks the best few accurately.
4. How do you chunk? 180 words with 30 overlap per page, so every chunk keeps a page number for citation.
5. How do you reduce hallucination? Answer only from numbered context, cite sources, say "not found" if absent.
6. What if there is no API key? Demo mode: real retrieval, extractive answer from top sentences.
7. Limitations? Scanned PDFs need OCR; tables and formulas extract poorly; page-level chunking can split sections; no multi-user login.
8. Future work? OCR, section-aware chunking, streaming answers, evaluation set (Recall@k), user accounts.
9. How is the vector store kept consistent? Each paper's chunks have the paper_id in metadata; deleting a paper removes its vectors and rebuilds BM25.
10. Why SQLite plus Chroma? SQLite holds the source text, metadata and history; Chroma holds vectors for fast similarity search.

## Demo script
1. Show the sidebar, upload a PDF, show the passage count.
2. Ask a factual question, then click a [n] chip to show the exact passage.
3. Tick only one paper and ask again to show scoped search.
4. Press Summarise. Explain the footer: demo mode vs LLM connected.
