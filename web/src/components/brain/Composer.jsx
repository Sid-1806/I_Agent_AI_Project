import { useState } from "react";
import { ArrowUp, Loader2 } from "lucide-react";

// Question input, with the scenario's own test questions as shortcuts.
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
        <div className="suggestions">
          {suggestions.map((q) => (
            <button key={q} type="button" className="suggestion" disabled={busy} onClick={() => send(q)} title="Ask this question">
              {q}
            </button>
          ))}
        </div>
      )}
      <form
        className="ask-field"
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
      >
        <textarea
          rows={1}
          value={text}
          placeholder={busy ? "The agent is working…" : "Ask the agent or give it a task, e.g. “Drive to Room 102”"}
          disabled={busy}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          aria-label="Question for the agent"
        />
        <button type="submit" className="send" disabled={busy || !text.trim()} aria-label="Send">
          {busy ? <Loader2 size={16} className="spin" /> : <ArrowUp size={16} strokeWidth={2.4} />}
        </button>
      </form>
    </div>
  );
}
