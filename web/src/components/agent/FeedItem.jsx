import { AlertTriangle, Bot, CheckCircle2, FilePen, MessageSquare, PlayCircle, ShieldAlert, Wrench } from "lucide-react";
import { Badge } from "../ui.jsx";
import { stepKind, toolResult } from "../../lib/format.js";

const ICON = {
  start: PlayCircle,
  question: MessageSquare,
  tool_call: Wrench,
  thought: Bot,
  draft: FilePen,
  self_check: ShieldAlert,
  answer: CheckCircle2,
  error: AlertTriangle,
};

// One step of the procedural layer, styled like an activity item; self-checks and refusals read as alerts.
export default function FeedItem({ frame, index, current, onSelect }) {
  const { label, tone } = stepKind(frame);
  const Icon = ICON[frame.type] || Bot;
  let title = frame.text;
  let body = null;
  if (frame.type === "tool_call") {
    const res = toolResult(frame);
    title = (
      <>
        <span className="chip-id">{frame.name}</span>
        {Object.entries(frame.args || {}).map(([k, v]) => (
          <span key={k} className="arg">
            {k}={String(v)}
          </span>
        ))}
      </>
    );
    body = (
      <>
        <div className={`tool-lines${res.error ? " error" : ""}`}>
          {res.lines.map((l, i) => (
            <div key={i}>{l}</div>
          ))}
        </div>
        {res.conflicts.length > 0 && (
          <div className="feed-warning">
            <AlertTriangle size={12} /> memory check: {res.conflicts.join("; ")}
          </div>
        )}
      </>
    );
  } else if (frame.type === "start") {
    title = "Fresh world and memory";
  } else if (frame.type === "self_check") {
    title = "Draft rejected by the self-check";
    body = <p>{frame.text}</p>;
  } else if (frame.type === "draft") {
    title = "Draft answer";
    body = <p>{frame.text}</p>;
  } else if (frame.type === "answer") {
    title = "Answer";
    body = <p>{frame.text}</p>;
  } else if (frame.type === "thought") {
    title = "Thinking";
    body = <p>{frame.text}</p>;
  }
  return (
    <li className={`feed-item kind-${frame.type} tone-${tone}${current ? " current" : ""}`}>
      <button type="button" onClick={onSelect} aria-current={current ? "step" : undefined}>
        <span className="feed-icon">
          <Icon size={15} strokeWidth={2} />
        </span>
        <span className="feed-main">
          <span className="feed-title">
            {frame.type === "question" ? <b>{frame.text}</b> : title}
          </span>
          {body && <span className="feed-body">{body}</span>}
        </span>
        <span className="feed-side">
          <Badge tone={tone}>{label}</Badge>
          <span className="mono">#{index}</span>
        </span>
      </button>
    </li>
  );
}
