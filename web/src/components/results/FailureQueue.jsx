import { AlertOctagon, AlertTriangle, Play } from "lucide-react";
import { Badge } from "../ui.jsx";
import { SET_LABEL, folderTime } from "../../lib/format.js";

// Failing full-system runs, like an alert queue: red when the answer itself was wrong,
// amber when the answer was right but a tool, memory or grounding check failed.
export default function FailureQueue({ items, onReplay }) {
  if (!items.length) return <p className="quiet">No failing runs for this version.</p>;
  return (
    <ul className="queue">
      {items.map((f) => {
        const critical = !f.answer_ok;
        const Icon = critical ? AlertOctagon : AlertTriangle;
        return (
          <li key={f.file} className={critical ? "critical" : "warning"}>
            <Icon size={16} strokeWidth={2} className="queue-icon" />
            <div className="queue-main">
              <div className="queue-title">
                <b>{f.scenario}</b>
                <Badge tone={critical ? "bad" : "warn"}>{critical ? "wrong answer" : "check failed"}</Badge>
              </div>
              <div className="queue-body">{f.failed.join(" · ")}</div>
              <div className="queue-meta mono">
                {SET_LABEL[f.set]} · {f.system} · {folderTime(f.folder)}
              </div>
            </div>
            <button type="button" className="icon-btn" onClick={() => onReplay(f.file)} aria-label={`Replay ${f.scenario}`} title="Replay this run">
              <Play size={14} />
            </button>
          </li>
        );
      })}
    </ul>
  );
}
