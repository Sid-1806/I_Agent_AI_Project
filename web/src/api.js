// Thin client for server.py.

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

export const getConfig = () => fetch("/api/config").then(json);
export const getScenarios = () => fetch("/api/scenarios").then(json);
export const getRuns = () => fetch("/api/runs").then(json);
export const getReplay = (file) => fetch(`/api/replay?file=${encodeURIComponent(file)}`).then(json);

export const newSession = (scenario, level) =>
  fetch("/api/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scenario, level }),
  }).then(json);

// Streams the agent's steps: onEvent is called with {event: "frame" | "done" | "error", ...}.
export async function ask(session, question, onEvent) {
  const res = await fetch(`/api/sessions/${session}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
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
