"""LLM layer. Real LLM when LLM_API_KEY is set, otherwise a local extractive DEMO mode."""
import httpx
from . import config
from .text_utils import keywords, split_sentences

SYSTEM = ("You are a research assistant. Answer ONLY from the numbered context passages. "
          "Cite sources inline like [1] or [2][3]. If the context does not contain the answer, "
          "say so. Be precise and concise.")


def mode():
    return "llm" if config.LLM_API_KEY else "demo"


def _call(system, user, max_tokens=900):
    if config.LLM_PROVIDER == "openai":
        base = config.LLM_BASE_URL or "https://api.openai.com/v1"
        r = httpx.post(f"{base}/chat/completions", timeout=90,
                       headers={"Authorization": f"Bearer {config.LLM_API_KEY}"},
                       json={"model": config.LLM_MODEL, "max_tokens": max_tokens,
                             "messages": [{"role": "system", "content": system},
                                          {"role": "user", "content": user}]})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    r = httpx.post("https://api.anthropic.com/v1/messages", timeout=90,
                   headers={"x-api-key": config.LLM_API_KEY, "anthropic-version": "2023-06-01",
                            "content-type": "application/json"},
                   json={"model": config.LLM_MODEL, "max_tokens": max_tokens, "system": system,
                         "messages": [{"role": "user", "content": user}]})
    r.raise_for_status()
    return "".join(b.get("text", "") for b in r.json()["content"])


def _demo_answer(question, contexts):
    q = set(keywords(question))
    scored = []
    for n, c in enumerate(contexts, start=1):
        for s in split_sentences(c["text"]):
            overlap = len(q & set(keywords(s)))
            if overlap:
                scored.append((overlap, n, s))
    scored.sort(key=lambda x: x[0], reverse=True)
    picked = scored[:3] or [(0, 1, split_sentences(contexts[0]["text"])[0] if
                             split_sentences(contexts[0]["text"]) else contexts[0]["text"][:250])]
    body = " ".join(f"{s} [{n}]" for _, n, s in picked)
    return ("Demo mode (no LLM key set), so this answer is stitched from the most relevant "
            "sentences retrieved:\n\n" + body)


def answer(question, contexts):
    if not contexts:
        return "I could not find anything relevant in the selected papers.", mode()
    if mode() == "demo":
        return _demo_answer(question, contexts), "demo"
    ctx = "\n\n".join(f"[{i}] ({c['title']}, p.{c['page']})\n{c['text']}"
                      for i, c in enumerate(contexts, start=1))
    try:
        return _call(SYSTEM, f"Context:\n{ctx}\n\nQuestion: {question}"), "llm"
    except Exception as e:
        return (f"The LLM call failed ({e}). Showing retrieval-only answer.\n\n"
                + _demo_answer(question, contexts)), "demo"


def summarize(title, chunks):
    if not chunks:
        return "No text found in this paper.", mode()
    step = max(1, len(chunks) // 8)
    sample = chunks[::step][:8]
    if mode() == "demo":
        lines = []
        for c in sample[:4]:
            sents = split_sentences(c["text"])
            if sents:
                lines.append("- " + sents[0])
        return "Demo mode summary (first key sentences from spread-out sections):\n\n" + "\n".join(lines), "demo"
    text = "\n\n".join(c["text"] for c in sample)
    prompt = (f"Summarise the research paper '{title}' from these excerpts. Give: Problem, Method, "
              f"Key results, Limitations. Use short bullet points.\n\n{text}")
    try:
        return _call("You summarise academic papers accurately.", prompt), "llm"
    except Exception as e:
        return f"Summary failed: {e}", "demo"
