import { AlertTriangle, Bot, CheckCircle2, FileEdit, MessageSquare, PlayCircle, ShieldX, Wrench } from "lucide-react";
import { stepKind, toolResult } from "../../lib/format.js";

const ICONS = {
  start: PlayCircle,
  question: MessageSquare,
  tool_call: Wrench,
  thought: Bot,
  draft: FileEdit,
  self_check: ShieldX,
  answer: CheckCircle2,
  error: AlertTriangle,
  note: Bot,
};

function Args({ args }) {
  const entries = Object.entries(args || {});
  if (!entries.length) return null;
  return (
    <div className="args">
      {entries.map(([k, v]) => (
        <span key={k} className="arg">
          <span className="muted">{k}</span> {String(v)}
        </span>
      ))}
    </div>
  );
}

// One step of the procedural layer. Selecting it shows the world and memory at that step.
export default function TraceRow({ frame, index, current, onSelect }) {
  const { label, tone } = stepKind(frame);
  const Icon = ICONS[frame.type] || Bot;
  let title;
  let body = null;
  if (frame.type === "tool_call") {
    const res = toolResult(frame);
    title = <span className="mono">{frame.name}</span>;
    body = (
      <>
        <Args args={frame.args} />
        <div className={`tool-result${res.error ? " error" : ""}`}>
          {res.lines.map((l, i) => (
            <div key={i}>{l}</div>
          ))}
        </div>
        {res.conflicts.length > 0 && (
          <div className="inline-warning">
            <AlertTriangle size={13} /> memory check: {res.conflicts.join("; ")}
          </div>
        )}
      </>
    );
  } else if (frame.type === "start") {
    title = "Fresh world and memory";
  } else if (frame.type === "question") {
    title = frame.text;
  } else if (frame.type === "self_check") {
    title = "Draft rejected";
    body = <p>{frame.text}</p>;
  } else if (frame.type === "draft") {
    title = "Draft answer";
    body = <p className="muted">{frame.text}</p>;
  } else if (frame.type === "answer") {
    title = "Final answer";
    body = <p>{frame.text}</p>;
  } else {
    title = label;
    body = <p className="muted">{frame.text}</p>;
  }
  return (
    <li className={`trace-row tone-edge-${tone}${current ? " current" : ""}${frame.type === "question" ? " question" : ""}`}>
      <button type="button" onClick={onSelect}>
        <div className="trace-head">
          <span className={`trace-icon tone-${tone}`}>
            <Icon size={14} strokeWidth={2} />
          </span>
          <span className={`trace-label tone-${tone}`}>{label}</span>
          <span className="trace-title">{title}</span>
          <span className="trace-step mono">#{index}</span>
        </div>
        {body && <div className="trace-body">{body}</div>}
      </button>
    </li>
  );
}
