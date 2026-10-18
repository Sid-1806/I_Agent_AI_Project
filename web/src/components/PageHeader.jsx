import { RotateCcw } from "lucide-react";
import { Badge, Chip, Segmented, Toggle } from "./ui.jsx";
import { SCENARIO_TYPES, SET_LABEL, scenarioTitle } from "../lib/format.js";

// Title, description, pickers and filters for the current view.
export default function PageHeader(props) {
  const { mode, scenario, busy, live, logs, follow, onFollow, overlay, onOverlay } = props;
  const { code, name } = scenarioTitle(scenario?.id);
  return (
    <div className="page-header">
      <div className="title-row">
        <div className="title">
          <h1>
            {scenario ? (
              <>
                <span className="code">{code}</span> {name}
              </>
            ) : mode === "logs" ? (
              "Test logs"
            ) : (
              "Loading"
            )}
          </h1>
          <p>
            {scenario && <Badge>{SET_LABEL[scenario.set] || scenario.set}</Badge>} {scenario?.description || (mode === "logs" ? "Choose a logged run to replay it step by step." : "")}
          </p>
        </div>
        <div className="title-controls">
          {mode === "live" ? (
            <>
              <select value={live.scenarioId} onChange={(e) => live.onScenario(e.target.value)} disabled={busy} aria-label="World">
                {live.scenarios
                  .filter((s) => live.type === "all" || s.type === live.type)
                  .map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.id} · {SET_LABEL[s.set]}
                    </option>
                  ))}
              </select>
              <button type="button" className="btn" onClick={live.onRestart} disabled={busy}>
                <RotateCcw size={14} strokeWidth={2} /> Reset world
              </button>
            </>
          ) : (
            <select value={logs.file} onChange={(e) => logs.onRun(e.target.value)} aria-label="Logged run">
              <option value="">Choose a logged run…</option>
              {[...new Set(logs.runs.map((r) => r.folder))].map((folder) => (
                <optgroup key={folder} label={folder}>
                  {logs.runs
                    .filter((r) => r.folder === folder && (logs.filter === "all" || (logs.filter === "passed") === !!r.passed))
                    .map((r) => (
                      <option key={r.file} value={r.file}>
                        {r.scenario} · {r.passed ? "passed" : "failed"}
                      </option>
                    ))}
                </optgroup>
              ))}
            </select>
          )}
        </div>
      </div>
      <div className="filter-row">
        <div className="chips">
          {mode === "live"
            ? SCENARIO_TYPES.map((t) => (
                <Chip
                  key={t.key}
                  active={live.type === t.key}
                  count={t.key === "all" ? live.scenarios.length : live.scenarios.filter((s) => s.type === t.key).length}
                  onClick={() => live.onType(t.key)}
                >
                  {t.label}
                </Chip>
              ))
            : ["all", "passed", "failed"].map((k) => (
                <Chip
                  key={k}
                  active={logs.filter === k}
                  count={k === "all" ? logs.runs.length : logs.runs.filter((r) => (k === "passed") === !!r.passed).length}
                  onClick={() => logs.onFilter(k)}
                >
                  {k[0].toUpperCase() + k.slice(1)}
                </Chip>
              ))}
        </div>
        <div className="filter-side">
          {mode === "live" && (
            <Segmented
              options={Object.entries(live.levels || {}).map(([k, v]) => ({ value: k, label: k === "full" ? "All safeguards" : k === "checks" ? "Tool checks only" : "No safeguards", title: v }))}
              value={live.level}
              onChange={live.onLevel}
              disabled={busy}
            />
          )}
          <Toggle label="Sensor card" checked={overlay} onChange={onOverlay} />
          <Toggle label="Follow latest" checked={follow} onChange={onFollow} />
        </div>
      </div>
    </div>
  );
}
