import { useState } from "react";

// Question input for live mode, with the scenario's own test questions as shortcuts.
export default function AskBox({ suggestions, busy, onAsk }) {
  const [text, setText] = useState("");
  const send = (q) => {
    const question = (q ?? text).trim();
    if (!question || busy) return;
    onAsk(question);
    setText("");
  };
  return (
    <div className="ask">
      {suggestions.length > 0 && (
        <div className="suggestions">
          <span className="muted">Scenario questions:</span>
          {suggestions.map((q) => (
            <button key={q} type="button" className="link" disabled={busy} onClick={() => send(q)}>
              {q}
            </button>
          ))}
        </div>
      )}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
      >
        <textarea
          rows={2}
          value={text}
          placeholder={busy ? "The agent is answering…" : "Ask the agent, e.g. “Is your route clear?”"}
          disabled={busy}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
        />
        <button type="submit" disabled={busy || !text.trim()}>
          {busy ? "Working" : "Send"}
        </button>
      </form>
    </div>
  );
}
