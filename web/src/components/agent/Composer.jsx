import { useState } from "react";
import { ArrowUp, Loader2 } from "lucide-react";

// Question box, with the scenario's own test questions as one-click shortcuts.
export default function Composer({ suggestions, busy, onAsk }) {
  const [text, setText] = useState("");
  const send = (q) => {
    const question = (q ?? text).trim();
    if (!question || busy) return;
    onAsk(question);
    setText("");
  };
  return (
    <div className="composer">
      {suggestions.length > 0 && (
        <div className="suggestions" aria-label="Scenario questions">
          {suggestions.map((q) => (
            <button key={q} type="button" className="suggestion" disabled={busy} onClick={() => send(q)} title={q}>
              {q}
            </button>
          ))}
        </div>
      )}
      <form
        className="ask"
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
      >
        <textarea
          rows={1}
          value={text}
          disabled={busy}
          placeholder={busy ? "The agent is working…" : "Ask the agent or give it a task"}
          aria-label="Question for the agent"
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
        />
        <button type="submit" className="send" disabled={busy || !text.trim()} aria-label="Send">
          {busy ? <Loader2 size={17} className="spin" /> : <ArrowUp size={17} strokeWidth={2.4} />}
        </button>
      </form>
    </div>
  );
}
