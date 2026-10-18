import { useCallback, useEffect, useState } from "react";
import { X } from "lucide-react";
import * as api from "./api.js";
import { useLiveSession, useReplay } from "./hooks.js";
import Rail from "./components/Rail.jsx";
import TopBar from "./components/TopBar.jsx";
import PageHeader from "./components/PageHeader.jsx";
import WorldCard from "./components/world/WorldCard.jsx";
import BrainCard from "./components/brain/BrainCard.jsx";
import MemoryCard from "./components/memory/MemoryCard.jsx";
import Timeline from "./components/Timeline.jsx";

// Two views over the same three layers:
//   live  talk to the agent in a scenario's world; each step streams in as it happens
//   logs  replay a logged evaluation run step by step
export default function App() {
  const [mode, setMode] = useState("live");
  const [config, setConfig] = useState(null);
  const [error, setError] = useState("");
  const [cursor, setCursor] = useState(0);
  const [follow, setFollow] = useState(true);
  const [overlay, setOverlay] = useState(true);
  const [type, setType] = useState("all");
  const [runFilter, setRunFilter] = useState("all");

  const onError = useCallback((e) => setError(e?.message || String(e)), []);
  const live = useLiveSession(onError);
  const logs = useReplay(mode === "logs", onError);

  useEffect(() => {
    api.getConfig().then(setConfig).catch(onError);
  }, [onError]);

  const frames = (mode === "live" ? live.session?.frames : logs.replay?.frames) || [];
  const scenario = mode === "live" ? live.session?.scenario : logs.replay?.scenario;
  const at = Math.min(cursor, Math.max(0, frames.length - 1));
  const frame = frames[at];
  const previous = at > 0 ? frames[at - 1] : null;

  useEffect(() => {
    if (follow && frames.length) setCursor(frames.length - 1);
  }, [frames.length, follow]);

  useEffect(() => {
    if (mode === "logs") {
      setFollow(false);
      setCursor(0);
    }
  }, [mode, logs.replay]);

  const select = (i) => {
    setCursor(i);
    if (i < frames.length - 1) setFollow(false);
  };

  return (
    <div className="shell">
      <Rail
        mode={mode}
        onMode={(m) => {
          setMode(m);
          setFollow(m === "live");
        }}
      />
      <div className="main">
        <TopBar frames={frames.slice(0, at + 1)} frame={frame} config={config} />
        <PageHeader
          mode={mode}
          scenario={scenario}
          busy={live.busy}
          follow={follow}
          onFollow={(v) => {
            setFollow(v);
            if (v) setCursor(frames.length - 1);
          }}
          overlay={overlay}
          onOverlay={setOverlay}
          live={{
            scenarios: live.scenarios,
            scenarioId: live.scenarioId,
            onScenario: live.setScenarioId,
            type,
            onType: setType,
            level: live.level,
            onLevel: live.setLevel,
            levels: config?.levels,
            onRestart: live.restart,
          }}
          logs={{ runs: logs.runs, file: logs.file, onRun: logs.open, filter: runFilter, onFilter: setRunFilter }}
        />
        {error && (
          <div className="error-bar" role="alert">
            <span>{error}</span>
            <button type="button" onClick={() => setError("")} aria-label="Dismiss">
              <X size={14} />
            </button>
          </div>
        )}
        {scenario ? (
          <div className="workspace">
            <div className="left">
              <WorldCard world={scenario.world} frames={frames} frame={frame} overlay={overlay} onOverlay={setOverlay} />
              <MemoryCard frame={frame} previous={previous} />
            </div>
            <BrainCard
              frames={frames}
              cursor={at}
              onSelect={select}
              live={mode === "live"}
              busy={live.busy}
              suggestions={scenario.turns || []}
              onAsk={(q) => {
                setFollow(true);
                live.ask(q);
              }}
              replay={mode === "logs" ? logs.replay : null}
            />
          </div>
        ) : (
          <div className="empty">{mode === "logs" ? "Choose a logged run above to replay it." : "Starting a session…"}</div>
        )}
        {frames.length > 0 && <Timeline frames={frames} cursor={at} onChange={select} />}
      </div>
    </div>
  );
}
