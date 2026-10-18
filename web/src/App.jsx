import { useCallback, useEffect, useState } from "react";
import * as api from "./api.js";
import TopBar from "./components/TopBar.jsx";
import StepBar from "./components/StepBar.jsx";
import WorldPanel from "./components/WorldPanel.jsx";
import BrainPanel from "./components/BrainPanel.jsx";
import MemoryPanel from "./components/MemoryPanel.jsx";

// Two modes over the same three panels:
//   live  a fresh world, memory and agent for a scenario; the user asks questions and every agent
//         step streams in as it happens
//   logs  a logged evaluation run, rebuilt step by step by the server
export default function App() {
  const [mode, setMode] = useState("live");
  const [config, setConfig] = useState(null);
  const [scenarios, setScenarios] = useState([]);
  const [scenarioId, setScenarioId] = useState("A1_route_blocked");
  const [level, setLevel] = useState("full");
  const [session, setSession] = useState(null);
  const [busy, setBusy] = useState(false);
  const [runs, setRuns] = useState([]);
  const [runFile, setRunFile] = useState("");
  const [replay, setReplay] = useState(null);
  const [cursor, setCursor] = useState(0);
  const [follow, setFollow] = useState(true);
  const [error, setError] = useState("");

  const fail = (e) => setError(e.message || String(e));

  useEffect(() => {
    api.getConfig().then(setConfig).catch(fail);
    api.getScenarios().then(setScenarios).catch(fail);
  }, []);

  const startSession = useCallback(async (id, lv) => {
    setError("");
    const s = await api.newSession(id, lv);
    setSession({ id: s.session, scenario: s.scenario, frames: s.frames });
    setCursor(0);
    setFollow(true);
  }, []);

  useEffect(() => {
    if (scenarios.length) startSession(scenarioId, level).catch(fail);
  }, [scenarios.length, scenarioId, level, startSession]);

  useEffect(() => {
    if (mode === "logs" && !runs.length) api.getRuns().then(setRuns).catch(fail);
  }, [mode, runs.length]);

  const frames = (mode === "live" ? session?.frames : replay?.frames) || [];
  const scenario = mode === "live" ? session?.scenario : replay?.scenario;

  useEffect(() => {
    if (follow && frames.length) setCursor(frames.length - 1);
  }, [frames.length, follow]);

  const select = (i) => {
    setCursor(i);
    setFollow(i >= frames.length - 1);
  };

  const onAsk = async (question) => {
    setBusy(true);
    setError("");
    setFollow(true);
    try {
      await api.ask(session.id, question, (ev) => {
        if (ev.event === "frame") setSession((s) => ({ ...s, frames: [...s.frames, ev.frame] }));
        if (ev.event === "error") setError(ev.message);
      });
    } catch (e) {
      fail(e);
    } finally {
      setBusy(false);
    }
  };

  const onRun = async (file) => {
    setRunFile(file);
    setReplay(null);
    if (!file) return;
    try {
      setError("");
      setReplay(await api.getReplay(file));
      setCursor(0);
      setFollow(false);
    } catch (e) {
      fail(e);
    }
  };

  const frame = frames[Math.min(cursor, frames.length - 1)];
  const previous = cursor > 0 ? frames[cursor - 1] : null;
  const failedChecks = replay?.checks?.filter((c) => !c.passed).map((c) => `${c.kind}: ${c.name}`) || [];

  return (
    <div className="app">
      <TopBar
        mode={mode}
        onMode={(m) => {
          setMode(m);
          setFollow(m === "live");
        }}
        config={config}
        scenarios={scenarios}
        scenarioId={scenarioId}
        onScenario={setScenarioId}
        level={level}
        onLevel={setLevel}
        onRestart={() => startSession(scenarioId, level).catch(fail)}
        runs={runs}
        runFile={runFile}
        onRun={onRun}
        busy={busy}
      />
      <div className="context">
        {scenario ? (
          <p>
            <strong>{scenario.id}</strong> <span className="muted">({scenario.set})</span> {scenario.description}
            {mode === "live" && level !== "full" && (
              <span className="warn"> Safeguards level “{level}”: {config?.levels?.[level]}.</span>
            )}
            {mode === "logs" && replay && (
              <span className="muted">
                {" "}
                Evaluation: {replay.passed ? "passed" : `failed (${failedChecks.join("; ")})`}. {replay.level} {replay.system}, {replay.model}.
              </span>
            )}
          </p>
        ) : (
          <p className="muted">{mode === "logs" ? "Choose a logged run." : "Loading…"}</p>
        )}
        {frames.length > 0 && <StepBar count={frames.length} cursor={Math.min(cursor, frames.length - 1)} onChange={select} />}
      </div>
      {error && (
        <div className="error-bar" role="alert">
          {error}
        </div>
      )}
      {scenario && (
        <main className="layers">
          <WorldPanel world={scenario.world} frames={frames} frame={frame} />
          <BrainPanel
            frames={frames}
            cursor={Math.min(cursor, frames.length - 1)}
            onSelect={select}
            live={mode === "live"}
            busy={busy}
            suggestions={scenario.turns || []}
            onAsk={onAsk}
          />
          <MemoryPanel frame={frame} previous={previous} />
        </main>
      )}
    </div>
  );
}
