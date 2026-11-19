"""Central configuration. All values can be overridden from backend/.env"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma"
DB_PATH = DATA_DIR / "app.db"
for d in (DATA_DIR, UPLOAD_DIR, CHROMA_DIR):
    d.mkdir(parents=True, exist_ok=True)

LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic").lower()
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-5-5")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "").rstrip("/")

EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
RERANK_MODEL = os.getenv("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

CHUNK_WORDS = 180      # words per chunk
CHUNK_STRIDE = 150     # step between chunks (=> 30 words overlap)
CANDIDATES = 20        # per retriever (dense / BM25) before fusion
TOP_K = 5              # final chunks sent to the LLM
