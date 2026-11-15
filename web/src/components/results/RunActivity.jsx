import { FolderClock } from "lucide-react";
import { LEVEL_LABEL, SET_LABEL, folderTime, pct } from "../../lib/format.js";

// Evaluation runs, newest first, like a recent-activity list.
export default function RunActivity({ folders }) {
  return (
    <ul className="activity">
      {folders.map((f) => (
        <li key={f.folder}>
          <span className="activity-icon">
            <FolderClock size={15} />
          </span>
          <div className="activity-main">
            <div className="activity-title">
              <span className="chip-id">{SET_LABEL[f.set] || f.set}</span>
              <span className="chip-id">{LEVEL_LABEL[f.level] || f.level}</span>
              <span className="chip-id">{f.system}</span>
              {f.temperature ? <span className="chip-id">T={f.temperature}</span> : null}
            </div>
            <div className="activity-meta mono">
              {folderTime(f.folder)} · {f.model}
            </div>
          </div>
          <div className="activity-score">
            <b>
              {f.passed}/{f.runs}
            </b>
            <span className="score-bar">
              <i style={{ width: `${pct(f.passed, f.runs)}%` }} />
            </span>
          </div>
        </li>
      ))}
    </ul>
  );
}
