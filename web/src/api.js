// Client for server.py.

async function json(res) {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail || detail;
    } catch {
      /* not JSON */
    }
    throw new Error(detail);
  }
  return res.json();
}

const post = (url, body) =>
  fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

export const getConfig = () => fetch("/api/config").then(json);
export const getScenarios = () => fetch("/api/scenarios").then(json);
export const getRuns = () => fetch("/api/runs").then(json);
export const getResults = () => fetch("/api/results").then(json);
export const getReplay = (file) => fetch(`/api/replay?file=${encodeURIComponent(file)}`).then(json);
export const newSession = (scenario, level) => post("/api/sessions", { scenario, level }).then(json);

// Streams the agent's steps; onEvent gets {event: "frame" | "done" | "error", ...}.
export async function ask(session, question, onEvent) {
  const res = await post(`/api/sessions/${session}/ask`, { question });
  if (!res.ok) await json(res);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let nl;
    while ((nl = buffer.indexOf("\n")) >= 0) {
      const line = buffer.slice(0, nl).trim();
      buffer = buffer.slice(nl + 1);
      if (line) onEvent(JSON.parse(line));
    }
  }
}
