import { useEffect, useRef, useState } from "react";

function Sources({ sources }) {
  const [open, setOpen] = useState(null);
  if (!sources?.length) return null;
  return (
    <div className="mt-3">
      <div className="flex flex-wrap gap-2">
        {sources.map((s) => (
          <button key={s.n} onClick={() => setOpen(open === s.n ? null : s.n)}
                  className={`text-xs px-2 py-1 rounded ${open === s.n ? "bg-ink text-white" : "bg-mark text-ink"}`}>
            [{s.n}] {s.title.slice(0, 32)}{s.title.length > 32 ? "…" : ""}, p.{s.page}
          </button>
        ))}
      </div>
      {open && (() => {
        const s = sources.find((x) => x.n === open);
        return (
          <div className="mt-2 border-l-4 border-mark bg-white px-4 py-3 text-sm text-slate-700 font-serif leading-relaxed">
            {s.text}
            <div className="font-sans text-xs text-slate-500 mt-2">
              relevance {s.score} · found by {[s.dense && "embeddings", s.sparse && "keywords"].filter(Boolean).join(" + ")}
            </div>
          </div>
        );
      })()}
    </div>
  );
}

export default function Chat({ messages, loading, onAsk, scopeLabel, hasPapers }) {
  const [text, setText] = useState("");
  const end = useRef(null);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

  function submit(e) {
    e.preventDefault();
    if (!text.trim() || loading) return;
    onAsk(text.trim());
    setText("");
  }

  return (
    <main className="flex-1 flex flex-col h-full min-w-0">
      <div className="flex-1 overflow-y-auto px-8 py-8">
        <div className="max-w-3xl mx-auto space-y-8">
          {messages.length === 0 && (
            <div className="pt-16">
              <h2 className="font-serif text-3xl">{hasPapers ? "What do you want to know?" : "Start by uploading a paper"}</h2>
              <p className="text-slate-600 mt-2 max-w-xl">
                {hasPapers
                  ? "Try: What problem does this paper solve? Which dataset was used? What are the limitations?"
                  : "Upload one or more PDFs in the sidebar. Text is split into passages, indexed, and searched when you ask."}
              </p>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i}>
              {m.role === "user" ? (
                <p className="font-medium text-slate2 border-b border-slate-300 pb-2">{m.text}</p>
              ) : (
                <div>
                  <div className={`answer font-serif text-lg leading-relaxed whitespace-pre-wrap ${m.error ? "text-red-700" : ""}`}>{m.text}</div>
                  <Sources sources={m.sources} />
                </div>
              )}
            </div>
          ))}
          {loading && <p className="text-slate-500 text-sm">Searching papers…</p>}
          <div ref={end} />
        </div>
      </div>

      <form onSubmit={submit} className="border-t border-slate-300 bg-white px-8 py-4">
        <div className="max-w-3xl mx-auto flex gap-3 items-center">
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={hasPapers ? `Ask about ${scopeLabel}` : "Upload a paper first"}
            disabled={!hasPapers}
            className="flex-1 border border-slate-300 rounded-md px-3 py-2.5 focus:border-teal2 outline-none disabled:bg-slate-100"
          />
          <button disabled={!hasPapers || loading || !text.trim()}
                  className="bg-teal2 text-white px-4 py-2.5 rounded-md font-medium disabled:opacity-50">
            Ask
          </button>
        </div>
      </form>
    </main>
  );
}
