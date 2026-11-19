import { useRef, useState } from "react";

export default function Sidebar({ papers, selected, onToggle, onUpload, onDelete, onSummary, health }) {
  const input = useRef(null);
  const [busy, setBusy] = useState(false);
  const [drag, setDrag] = useState(false);

  async function handleFiles(files) {
    setBusy(true);
    for (const f of files) await onUpload(f);
    setBusy(false);
  }

  return (
    <aside className="w-80 shrink-0 bg-ink text-slate-100 flex flex-col h-full">
      <div className="px-5 pt-6 pb-4">
        <h1 className="font-serif text-xl leading-snug">Research Paper Assistant</h1>
        <p className="text-sm text-slate-400 mt-1">Ask questions across your PDFs and see the exact page behind every answer.</p>
      </div>

      <div className="px-5">
        <div
          onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false); handleFiles([...e.dataTransfer.files]); }}
          className={`border border-dashed rounded-md px-4 py-5 text-center text-sm transition-colors ${
            drag ? "border-mark bg-slate2" : "border-slate-500"
          }`}
        >
          <button
            onClick={() => input.current.click()}
            disabled={busy}
            className="bg-mark text-ink font-medium px-3 py-1.5 rounded disabled:opacity-60"
          >
            {busy ? "Indexing…" : "Upload PDF"}
          </button>
          <p className="text-slate-400 mt-2">or drop files here</p>
          <input ref={input} type="file" accept="application/pdf" multiple hidden
                 onChange={(e) => { handleFiles([...e.target.files]); e.target.value = ""; }} />
        </div>
      </div>

      <div className="px-5 pt-5 pb-2 text-sm text-slate-400">
        {papers.length ? `${selected.length || "All"} of ${papers.length} papers searched` : "No papers yet"}
      </div>

      <ul className="flex-1 overflow-y-auto px-3 pb-3 space-y-1">
        {papers.map((p) => (
          <li key={p.id} className="rounded-md px-2 py-2 hover:bg-slate2">
            <label className="flex gap-2 items-start cursor-pointer">
              <input type="checkbox" className="mt-1 accent-yellow-300"
                     checked={selected.includes(p.id)} onChange={() => onToggle(p.id)} />
              <span className="text-sm leading-snug">
                {p.title}
                <span className="block text-xs text-slate-400 mt-0.5">{p.pages} pages · {p.n_chunks} passages</span>
              </span>
            </label>
            <div className="flex gap-3 pl-6 mt-1 text-xs">
              <button onClick={() => onSummary(p)} className="text-mark hover:underline">Summarise</button>
              <button onClick={() => onDelete(p)} className="text-slate-400 hover:text-red-300">Remove</button>
            </div>
          </li>
        ))}
      </ul>

      {health && (
        <div className="px-5 py-3 text-xs text-slate-400 border-t border-slate-700">
          {health.mode === "llm" ? "LLM connected" : "Demo mode: add LLM_API_KEY in backend/.env"}
          <br />Search: {health.embedder === "minilm" ? "MiniLM embeddings" : "hash embeddings"} + BM25 + {health.reranker} reranker
        </div>
      )}
    </aside>
  );
}
