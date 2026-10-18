// Mode switch and the pickers for each mode.
export default function TopBar({ mode, onMode, config, scenarios, scenarioId, onScenario, level, onLevel, onRestart, runs, runFile, onRun, busy }) {
  return (
    <header className="topbar">
      <h1>I, Agent</h1>
      <div className="tabs" role="tablist">
        <button type="button" role="tab" aria-selected={mode === "live"} className={mode === "live" ? "on" : ""} onClick={() => onMode("live")}>
          Talk to the agent
        </button>
        <button type="button" role="tab" aria-selected={mode === "logs"} className={mode === "logs" ? "on" : ""} onClick={() => onMode("logs")}>
          Test logs
        </button>
      </div>
      {mode === "live" ? (
        <>
          <label>
            World
            <select value={scenarioId} onChange={(e) => onScenario(e.target.value)} disabled={busy}>
              {["dev", "heldout", "heldout2"].map((set) => (
                <optgroup key={set} label={set}>
                  {scenarios
                    .filter((s) => s.set === set)
                    .map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.id}
                      </option>
                    ))}
                </optgroup>
              ))}
            </select>
          </label>
          <label>
            Safeguards
            <select value={level} onChange={(e) => onLevel(e.target.value)} disabled={busy}>
              {Object.entries(config?.levels || {}).map(([k, v]) => (
                <option key={k} value={k} title={v}>
                  {k}
                </option>
              ))}
            </select>
          </label>
          <button type="button" onClick={onRestart} disabled={busy}>
            Reset world
          </button>
        </>
      ) : (
        <label>
          Run
          <select value={runFile} onChange={(e) => onRun(e.target.value)}>
            <option value="">Choose a logged run…</option>
            {[...new Set(runs.map((r) => r.folder))].map((folder) => (
              <optgroup key={folder} label={folder}>
                {runs
                  .filter((r) => r.folder === folder)
                  .map((r) => (
                    <option key={r.file} value={r.file}>
                      {r.scenario} · {r.passed ? "passed" : "failed"}
                    </option>
                  ))}
              </optgroup>
            ))}
          </select>
        </label>
      )}
      <span className="muted model">{config ? `${config.provider} · ${config.model}` : "connecting…"}</span>
    </header>
  );
}
