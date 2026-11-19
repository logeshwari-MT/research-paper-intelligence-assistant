"""SQLite storage: papers, text chunks and chat history."""
import json
import sqlite3
from contextlib import contextmanager
from . import config


@contextmanager
def conn():
    c = sqlite3.connect(config.DB_PATH)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init():
    with conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS papers(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              title TEXT, filename TEXT, pages INTEGER, n_chunks INTEGER,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS chunks(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              paper_id INTEGER, page INTEGER, text TEXT);
            CREATE TABLE IF NOT EXISTS messages(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              question TEXT, answer TEXT, sources TEXT, mode TEXT,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP);
            """
        )


def add_paper(title, filename, pages):
    with conn() as c:
        cur = c.execute("INSERT INTO papers(title, filename, pages, n_chunks) VALUES (?,?,?,0)",
                        (title, filename, pages))
        return cur.lastrowid


def add_chunks(paper_id, items):
    """items: list of (page, text). Returns list of (chunk_id, page, text)."""
    out = []
    with conn() as c:
        for page, text in items:
            cur = c.execute("INSERT INTO chunks(paper_id, page, text) VALUES (?,?,?)",
                            (paper_id, page, text))
            out.append((cur.lastrowid, page, text))
        c.execute("UPDATE papers SET n_chunks=? WHERE id=?", (len(items), paper_id))
    return out


def list_papers():
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM papers ORDER BY id DESC")]


def get_paper(paper_id):
    with conn() as c:
        r = c.execute("SELECT * FROM papers WHERE id=?", (paper_id,)).fetchone()
        return dict(r) if r else None


def paper_chunks(paper_id):
    with conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM chunks WHERE paper_id=? ORDER BY id", (paper_id,))]


def all_chunks():
    with conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT ch.id, ch.paper_id, ch.page, ch.text, p.title "
            "FROM chunks ch JOIN papers p ON p.id = ch.paper_id ORDER BY ch.id")]


def delete_paper(paper_id):
    with conn() as c:
        c.execute("DELETE FROM chunks WHERE paper_id=?", (paper_id,))
        c.execute("DELETE FROM papers WHERE id=?", (paper_id,))


def save_message(question, answer, sources, mode):
    with conn() as c:
        c.execute("INSERT INTO messages(question, answer, sources, mode) VALUES (?,?,?,?)",
                  (question, answer, json.dumps(sources), mode))


def history(limit=50):
    with conn() as c:
        rows = c.execute("SELECT * FROM messages ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    out = []
    for r in reversed(rows):
        d = dict(r)
        d["sources"] = json.loads(d["sources"] or "[]")
        out.append(d)
    return out


def clear_history():
    with conn() as c:
        c.execute("DELETE FROM messages")
