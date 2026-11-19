"""FastAPI entry point.  Run:  uvicorn app.main:app --reload --port 8000"""
import shutil
import uuid
from typing import List, Optional
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from . import config, db, llm
from .retrieval import Retriever
from .text_utils import chunk_pages, extract_pdf

db.init()
app = FastAPI(title="Research Paper Intelligence Assistant")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["*"], allow_headers=["*"])
retriever = Retriever()


class ChatIn(BaseModel):
    question: str
    paper_ids: Optional[List[int]] = None


@app.get("/api/health")
def health():
    return {"status": "ok", "mode": llm.mode(), "embedder": retriever.embedder.name,
            "reranker": "cross-encoder" if retriever.reranker.model else "lexical",
            "chunks_indexed": retriever.col.count()}


@app.get("/api/papers")
def papers():
    return db.list_papers()


@app.post("/api/papers/upload")
def upload(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported.")
    saved = config.UPLOAD_DIR / f"{uuid.uuid4().hex}.pdf"
    with open(saved, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        title, pages = extract_pdf(saved)
    except Exception as e:
        saved.unlink(missing_ok=True)
        raise HTTPException(400, f"Could not read this PDF: {e}")
    if not pages:
        saved.unlink(missing_ok=True)
        raise HTTPException(400, "No selectable text found. Scanned PDFs need OCR first.")
    chunks = chunk_pages(pages)
    paper_id = db.add_paper(title, file.filename, len(pages))
    rows = db.add_chunks(paper_id, chunks)
    retriever.index_chunks(paper_id, rows)
    return db.get_paper(paper_id)


@app.delete("/api/papers/{paper_id}")
def delete_paper(paper_id: int):
    if not db.get_paper(paper_id):
        raise HTTPException(404, "Paper not found")
    retriever.remove_paper(paper_id)
    db.delete_paper(paper_id)
    return {"deleted": paper_id}


@app.post("/api/papers/{paper_id}/summary")
def summary(paper_id: int):
    paper = db.get_paper(paper_id)
    if not paper:
        raise HTTPException(404, "Paper not found")
    text, m = llm.summarize(paper["title"], db.paper_chunks(paper_id))
    return {"summary": text, "mode": m}


@app.post("/api/chat")
def chat(body: ChatIn):
    q = body.question.strip()
    if not q:
        raise HTTPException(400, "Question is empty")
    hits = retriever.search(q, body.paper_ids or None)
    text, m = llm.answer(q, hits)
    sources = [{"n": i, "title": h["title"], "page": h["page"], "text": h["text"],
                "score": h["score"], "dense": h["in_dense"], "sparse": h["in_sparse"]}
               for i, h in enumerate(hits, start=1)]
    db.save_message(q, text, sources, m)
    return {"answer": text, "sources": sources, "mode": m}


@app.get("/api/history")
def history():
    return db.history()


@app.delete("/api/history")
def clear_history():
    db.clear_history()
    return {"cleared": True}
