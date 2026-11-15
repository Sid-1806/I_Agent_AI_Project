import { useState } from "react";
import { Ban, Database, FileText, RotateCcw, ShieldAlert, Wrench } from "lucide-react";
import StatBar from "../components/shell/StatBar.jsx";
import PageHeader from "../components/shell/PageHeader.jsx";
import LayersView, { stepStats } from "./LayersView.jsx";
import { Chip, Empty, Segmented, Select, Toggle } from "../components/ui.jsx";
import { useLiveSession, usePlayer } from "../hooks.js";
import { SCENARIO_TYPES, SET_LABEL, scenarioTitle } from "../lib/format.js";

const LEVEL_NAMES = { full: "All safeguards", checks: "Tool checks only", plain: "No safeguards" };

// Talk to the agent in any scenario's world and watch all three layers as it works.
export default function OperationsPage({ config, scenarios, onError }) {
  const [scenarioId, setScenarioId] = useState("A1_route_blocked");
  const [type, setType] = useState("all");
  const [level, setLevel] = useState("full");
  const [showRobot, setShowRobot] = useState(true);
  const live = useLiveSession(scenarioId, level, onError);
  const frames = live.session?.frames || [];
  const player = usePlayer(frames.length);
  const scenario = live.session?.scenario;
  const s = stepStats(frames, player.at);
  const { code, name } = scenarioTitle(scenario?.id);
  const visible = scenarios.filter((x) => type === "all" || x.type === type);

  return (
    <div className="page">
      <StatBar
        config={config}
        stats={[
          { icon: Wrench, label: "Tool calls", value: s.tools },
          { icon: ShieldAlert, label: "Self-checks", value: s.checks },
          { icon: Ban, label: "Refused", value: s.refused },
          { icon: Database, label: "Beliefs", value: s.beliefs },
          { icon: FileText, label: "Log records", value: s.records },
        ]}
      />
      <PageHeader
        title={
          scenario ? (
            <>
              <span className="title-code">{code}</span> {name}
            </>
          ) : (
            "Operations"
          )
        }
        subtitle={scenario && `${SET_LABEL[scenario.set]} · ${scenario.description}`}
        controls={
          <>
            <Select value={scenarioId} onChange={setScenarioId} label="World" disabled={live.busy}>
              {(visible.some((x) => x.id === scenarioId) ? visible : [scenarios.find((x) => x.id === scenarioId), ...visible])
                .filter(Boolean)
                .map((x) => (
                  <option key={x.id} value={x.id}>
                    {x.id} · {SET_LABEL[x.set]}
                  </option>
                ))}
            </Select>
            <button type="button" className="btn" onClick={() => { live.restart(); player.reset(); }} disabled={live.busy}>
              <RotateCcw size={14} /> Reset world
            </button>
          </>
        }
        filters={SCENARIO_TYPES.map((t) => (
          <Chip key={t.key} active={type === t.key} onClick={() => setType(t.key)} count={t.key === "all" ? scenarios.length : scenarios.filter((x) => x.type === t.key).length}>
            {t.label}
          </Chip>
        ))}
        side={
          <>
            <Segmented
              label="Safeguards"
              value={level}
              onChange={setLevel}
              disabled={live.busy}
              options={Object.entries(config?.levels || {}).map(([k, v]) => ({ value: k, label: LEVEL_NAMES[k] || k, title: v }))}
            />
            <Toggle label="Robot card" checked={showRobot} onChange={setShowRobot} />
            <Toggle label="Follow latest" checked={player.follow} onChange={(v) => { player.setFollow(v); if (v) player.go(frames.length - 1); }} />
          </>
        }
      />
      {scenario ? (
        <LayersView
          world={scenario.world}
          frames={frames}
          player={player}
          showRobot={showRobot}
          onShowRobot={setShowRobot}
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
