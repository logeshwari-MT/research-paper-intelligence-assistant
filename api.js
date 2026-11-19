// Thin wrapper around the FastAPI backend (proxied through Vite at /api).
async function request(path, options = {}) {
  const res = await fetch(`/api${path}`, options);
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch { /* ignore */ }
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  health: () => request("/health"),
  papers: () => request("/papers"),
  upload: (file) => {
    const form = new FormData();
    form.append("file", file);
    return request("/papers/upload", { method: "POST", body: form });
  },
  remove: (id) => request(`/papers/${id}`, { method: "DELETE" }),
  summary: (id) => request(`/papers/${id}/summary`, { method: "POST" }),
  chat: (question, paperIds) =>
    request("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, paper_ids: paperIds }),
    }),
  history: () => request("/history"),
  clearHistory: () => request("/history", { method: "DELETE" }),
};
