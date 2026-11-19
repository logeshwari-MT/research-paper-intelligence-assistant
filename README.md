# Research Paper Intelligence Assistant (Advanced RAG + LLM)

Upload research PDFs, ask questions in plain English, and get answers with citations
that point to the exact paper and page.

Stack: React + Vite + Tailwind (frontend), FastAPI (backend), ChromaDB (vector store),
BM25 (keyword search), cross-encoder reranking, SQLite (papers, chunks, chat history).

## 1. Run it in VS Code

You need Python 3.10+ and Node.js 18+. Open the project folder in VS Code and use two terminals.

### Terminal 1: backend
```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\activate        Mac/Linux:  source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # Windows: copy .env.example .env
uvicorn app.main:app --reload --port 8000
```
First start downloads two small models (about 120 MB) from Hugging Face, so it needs internet once.
If the install is too heavy, delete the `sentence-transformers` line in `requirements.txt`.
The app then runs in lite mode (hashing embeddings + lexical reranker).

### Terminal 2: frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173

## 2. Demo mode and adding your LLM key later
With `LLM_API_KEY` empty the app runs in demo mode: retrieval is fully real, and the
answer is stitched from the best-matching sentences, with citations. Everything works for a demo.

To switch to a real LLM, edit `backend/.env`:
```
LLM_API_KEY=your-key-here
LLM_PROVIDER=anthropic      # or openai (also works for OpenAI-compatible servers)
LLM_MODEL=claude-sonnet-5-5
```
Restart the backend. The sidebar footer shows "LLM connected".

## 3. How to use
1. Upload one or more text-based PDFs (scanned PDFs need OCR first).
2. Tick papers in the sidebar to limit the search, or leave all unticked to search everything.
3. Ask a question. Click a yellow [n] chip to see the exact passage behind that citation.
4. "Summarise" on a paper gives problem, method, results and limitations.

## 4. API
| Method | Path | Purpose |
|---|---|---|
| GET | /api/health | mode, models, indexed chunk count |
| GET | /api/papers | list papers |
| POST | /api/papers/upload | upload and index a PDF |
| DELETE | /api/papers/{id} | remove a paper |
| POST | /api/papers/{id}/summary | summarise a paper |
| POST | /api/chat | `{question, paper_ids?}` returns answer + sources |
| GET / DELETE | /api/history | chat history |

Interactive docs: http://localhost:8000/docs

## 5. Folder structure
```
backend/app/
  main.py        API routes
  config.py      settings from .env
  db.py          SQLite (papers, chunks, messages)
  text_utils.py  PDF parsing, chunking
  models.py      embedder + reranker (with fallbacks)
  retrieval.py   hybrid search: Chroma + BM25 + RRF + rerank
  llm.py         LLM call / demo mode
frontend/src/    App.jsx, api.js, components/Sidebar.jsx, components/Chat.jsx
docs/architecture.md
VIVA.md
```

## 6. Troubleshooting
- "Cannot reach the backend": start uvicorn first (port 8000).
- Upload says no selectable text: the PDF is scanned images; run OCR first.
- Model download fails (offline): the app falls back to lite mode automatically.
- Changed embedding model: old vectors are ignored because each embedder uses its own Chroma collection; re-upload papers.
