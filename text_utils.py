"""PDF parsing, chunking and tokenisation helpers."""
import re
from pypdf import PdfReader
from . import config

STOPWORDS = set("""a an the of and or to in on for with by is are was were be been this that these those
it its as at from which what who whom how why when where do does did can could should would will
about into over under than then there their they them we our you your i not no yes if but also""".split())


def tokenize(text: str):
    return re.findall(r"[a-z0-9]+", text.lower())


def keywords(text: str):
    return [t for t in tokenize(text) if t not in STOPWORDS and len(t) > 1]


def extract_pdf(path):
    """Returns (title, [(page_number, text), ...])."""
    reader = PdfReader(str(path))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            txt = page.extract_text() or ""
        except Exception:
            txt = ""
        txt = re.sub(r"-\n(\w)", r"\1", txt)      # re-join hyphenated words
        txt = re.sub(r"\s+", " ", txt).strip()
        if txt:
            pages.append((i, txt))
    title = None
    try:
        title = (reader.metadata.title or "").strip() if reader.metadata else None
    except Exception:
        pass
    if not title and pages:
        title = pages[0][1][:90].strip()
    return title or "Untitled paper", pages


def chunk_pages(pages):
    """Sliding word window per page. Returns [(page, text)]."""
    chunks = []
    for page, text in pages:
        words = text.split()
        start = 0
        while start < len(words):
            piece = words[start:start + config.CHUNK_WORDS]
            if len(piece) >= 20 or (start == 0 and piece):
                chunks.append((page, " ".join(piece)))
            if start + config.CHUNK_WORDS >= len(words):
                break
            start += config.CHUNK_STRIDE
    return chunks


def split_sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 25]
