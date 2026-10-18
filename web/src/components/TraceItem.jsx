import { toolSummary } from "../lib/format.js";

const TAGS = {
  start: ["START", "t-muted"],
  thought: ["THOUGHT", "t-muted"],
  draft: ["DRAFT", "t-muted"],
  self_check: ["SELF-CHECK", "t-bad"],
  answer: ["ANSWER", "t-good"],
  note: ["NOTE", "t-muted"],
  error: ["ERROR", "t-bad"],
};

// One step of the procedural layer. Clicking it shows the world and memory at that step.
export default function TraceItem({ frame, current, onSelect }) {
  const cls = `trace-item${current ? " current" : ""}`;
  if (frame.type === "question") {
    return (
      <li className={`${cls} question`} onClick={onSelect}>
        User: {frame.text}
      </li>
    );
  }
  if (frame.type === "tool_call") {
    const { text, error } = toolSummary(frame);
    const args = frame.args && Object.keys(frame.args).length ? JSON.stringify(frame.args) : "";
    return (
      <li className={cls} onClick={onSelect}>
        <span className="tag">TOOL</span>
        <span className="code">
          {frame.name}({args})
        </span>
        <div className={`result${error ? " error" : ""}`}>{text}</div>
        {frame.mismatch && <div className="result error">replayed result differs from the log</div>}
      </li>
    );
  }
  const [label, tone] = TAGS[frame.type] || [frame.type.toUpperCase(), "t-muted"];
  const text = frame.type === "start" ? "Fresh world and memory." : frame.type === "self_check" ? `Draft rejected. ${frame.text}` : frame.text;
  return (
    <li className={cls} onClick={onSelect}>
      <span className={`tag ${tone}`}>{label}</span>
      <span className={frame.type === "draft" ? "muted" : ""}>{text}</span>
    </li>
  );
}
