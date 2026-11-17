import { AlertTriangle } from "lucide-react";
import { stepKind, toolResult } from "../../lib/format.js";

// One step of the procedural layer. Self-checks, drafts and answers are tinted.
export default function FeedItem({ frame, current, onSelect }) {
  const { label, tone } = stepKind(frame);
  let title = frame.text;
  let body = null;
  if (frame.type === "tool_call") {
    const res = toolResult(frame);
    const args = Object.entries(frame.args || {}).map(([k, v]) => `${k}=${v}`).join(", ");
    title = <span className="mono">{frame.name}({args})</span>;
    body = (
      <>
        <div className={`tool-lines${res.error ? " error" : ""}`}>{res.lines.join("\n")}</div>
        {res.conflicts.length > 0 && (
          <div className="feed-warning">
            <AlertTriangle size={12} /> memory check: {res.conflicts.join("; ")}
          </div>
        )}
      </>
    );
  } else if (frame.type === "start") {
    title = "Fresh world and memory";
  } else if (["self_check", "draft", "answer", "thought"].includes(frame.type)) {
    title = null;
    body = <p>{frame.type === "self_check" ? `Draft rejected. ${frame.text}` : frame.text}</p>;
  }
  return (
    <li className={`feed-item kind-${frame.type}${current ? " current" : ""}`}>
      <button type="button" onClick={onSelect} aria-current={current ? "step" : undefined}>
        <span className={`feed-label tone-${tone}`}>{label}</span>
        {title && <span className="feed-title">{title}</span>}
        {body && <span className="feed-body">{body}</span>}
      </button>
    </li>
  );
}
