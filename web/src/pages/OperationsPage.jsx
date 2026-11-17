import { useState } from "react";
import { RotateCcw } from "lucide-react";
import PageHeader from "../components/shell/PageHeader.jsx";
import LayersView from "./LayersView.jsx";
import { Empty, Segmented, Select } from "../components/ui.jsx";
import { useLiveSession, usePlayer } from "../hooks.js";
import { SET_LABEL, scenarioTitle } from "../lib/format.js";

const LEVEL_NAMES = { full: "All safeguards", checks: "Tool checks only", plain: "No safeguards" };

// Talk to the agent in any scenario's world and watch all three layers as it works.
export default function OperationsPage({ config, scenarios, onError }) {
  const [scenarioId, setScenarioId] = useState("A1_route_blocked");
  const [level, setLevel] = useState("full");
  const live = useLiveSession(scenarioId, level, onError);
  const frames = live.session?.frames || [];
  const player = usePlayer(frames.length);
  const scenario = live.session?.scenario;
  const { code, name } = scenarioTitle(scenario?.id);

  return (
    <div className="page">
      <PageHeader
        title={scenario ? <><span className="title-code">{code}</span> {name}</> : "Talk to the agent"}
        subtitle={scenario?.description}
        controls={
          <>
            <Select value={scenarioId} onChange={setScenarioId} label="World" disabled={live.busy}>
              {scenarios.map((x) => (
                <option key={x.id} value={x.id}>
                  {x.id} · {SET_LABEL[x.set]}
                </option>
              ))}
            </Select>
            <Segmented
              label="Safeguards"
              value={level}
              onChange={setLevel}
              disabled={live.busy}
              options={Object.entries(config?.levels || {}).map(([k, v]) => ({ value: k, label: LEVEL_NAMES[k] || k, title: v }))}
            />
            <button type="button" className="btn" onClick={() => { live.restart(); player.reset(); }} disabled={live.busy}>
              <RotateCcw size={14} /> Reset
            </button>
          </>
        }
      />
      {scenario ? (
        <LayersView
          world={scenario.world}
          frames={frames}
          player={player}
          agentStatus={live.busy ? { tone: "warn", label: "working" } : { tone: "good", label: "ready" }}
          composer={{
            suggestions: scenario.turns || [],
            busy: live.busy,
            onAsk: (q) => {
              player.setFollow(true);
              live.ask(q);
            },
          }}
        />
      ) : (
        <Empty>Starting a session…</Empty>
      )}
    </div>
  );
}
