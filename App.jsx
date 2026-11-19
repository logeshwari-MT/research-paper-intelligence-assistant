import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import Sidebar from "./components/Sidebar.jsx";
import Chat from "./components/Chat.jsx";

export default function App() {
  const [papers, setPapers] = useState([]);
  const [selected, setSelected] = useState([]);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [health, setHealth] = useState(null);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      setPapers(await api.papers());
      setHealth(await api.health());
      setError("");
    } catch {
      setError("Cannot reach the backend. Start it with: uvicorn app.main:app --reload --port 8000");
    }
  }, []);

  useEffect(() => {
    refresh();
    api.history().then((h) =>
      setMessages(h.flatMap((r) => [
        { role: "user", text: r.question },
        { role: "assistant", text: r.answer, sources: r.sources },
      ]))
    ).catch(() => {});
  }, [refresh]);

  const push = (m) => setMessages((prev) => [...prev, m]);

  async function upload(file) {
    try { await api.upload(file); await refresh(); }
    catch (e) { setError(`${file.name}: ${e.message}`); }
  }

  async function remove(p) {
    if (!confirm(`Remove "${p.title}"?`)) return;
    await api.remove(p.id);
    setSelected((s) => s.filter((id) => id !== p.id));
    refresh();
  }

  async function summarise(p) {
    push({ role: "user", text: `Summarise: ${p.title}` });
    setLoading(true);
    try {
      const r = await api.summary(p.id);
      push({ role: "assistant", text: r.summary });
    } catch (e) { push({ role: "assistant", text: e.message, error: true }); }
    setLoading(false);
  }

  async function ask(question) {
    push({ role: "user", text: question });
    setLoading(true);
    try {
      const r = await api.chat(question, selected.length ? selected : null);
      push({ role: "assistant", text: r.answer, sources: r.sources });
    } catch (e) { push({ role: "assistant", text: e.message, error: true }); }
    setLoading(false);
  }

  const toggle = (id) => setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));
  const scopeLabel = selected.length ? `${selected.length} selected paper(s)` : "all papers";

  return (
    <div className="h-full flex flex-col">
      {error && (
        <div className="bg-red-100 text-red-800 text-sm px-4 py-2 flex justify-between">
          <span>{error}</span>
          <button onClick={() => setError("")} aria-label="Dismiss">✕</button>
        </div>
      )}
      <div className="flex-1 flex min-h-0">
        <Sidebar papers={papers} selected={selected} onToggle={toggle} onUpload={upload}
                 onDelete={remove} onSummary={summarise} health={health} />
        <Chat messages={messages} loading={loading} onAsk={ask}
              scopeLabel={scopeLabel} hasPapers={papers.length > 0} />
      </div>
    </div>
  );
}
