import { useEffect, useState } from "react";
import { Ban, CheckCircle2, Database, FileText, ShieldAlert, Wrench, XCircle } from "lucide-react";
import StatBar from "../components/shell/StatBar.jsx";
import PageHeader from "../components/shell/PageHeader.jsx";
import LayersView, { stepStats } from "./LayersView.jsx";
import { Chip, Empty, Select, Toggle } from "../components/ui.jsx";
import { usePlayer } from "../hooks.js";
import * as api from "../api.js";
import { SET_LABEL, folderTime, scenarioTitle } from "../lib/format.js";

function Checks({ replay }) {
  const failed = replay.checks.filter((c) => !c.passed);
  return (
    <div className={`checks ${replay.passed ? "ok" : "fail"}`}>
      <div className="checks-head">
        {replay.passed ? <CheckCircle2 size={15} /> : <XCircle size={15} />}
        Automatic checks: {replay.checks.length - failed.length} of {replay.checks.length} passed
      </div>
      {failed.map((c, i) => (
        <div key={i} className="checks-row">
          {c.kind}: {c.name} {c.detail}
        </div>
      ))}
    </div>
  );
}

// Step through any logged evaluation run, rebuilt by the server without calling the LLM.
export default function ReplayPage({ config, file, onFile, onError }) {
  const [runs, setRuns] = useState([]);
  const [filter, setFilter] = useState("all");
  const [replay, setReplay] = useState(null);
  const [showRobot, setShowRobot] = useState(true);
  const frames = replay?.frames || [];
  const player = usePlayer(frames.length, { followByDefault: false });

  useEffect(() => {
    api.getRuns().then(setRuns).catch(onError);
  }, [onError]);

  useEffect(() => {
    setReplay(null);
    player.reset();
    if (file) api.getReplay(file).then(setReplay).catch(onError);
  }, [file]); // eslint-disable-line react-hooks/exhaustive-deps

  const s = stepStats(frames, player.at);
  const scenario = replay?.scenario;
  const { code, name } = scenarioTitle(scenario?.id);
  const shown = runs.filter((r) => filter === "all" || (filter === "passed") === !!r.passed);
  const folders = [...new Set(shown.map((r) => r.folder))];

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
            "Replay"
          )
        }
        subtitle={
          scenario
            ? `${SET_LABEL[scenario.set]} · system ${replay.system} · ${replay.level} · ${replay.model}`
            : "Choose a logged run to replay it step by step. The LLM is not called; the layers are rebuilt from the log."
        }
        controls={
          <Select value={file} onChange={onFile} label="Logged run">
            <option value="">Choose a logged run…</option>
            {folders.map((f) => (
              <optgroup key={f} label={`${folderTime(f)} · ${f.split("_").slice(1).join(" · ")}`}>
                {shown
                  .filter((r) => r.folder === f)
                  .map((r) => (
                    <option key={r.file} value={r.file}>
                      {r.scenario} · {r.passed ? "passed" : "failed"}
                    </option>
                  ))}
              </optgroup>
            ))}
          </Select>
        }
        filters={["all", "passed", "failed"].map((k) => (
          <Chip key={k} active={filter === k} onClick={() => setFilter(k)} count={k === "all" ? runs.length : runs.filter((r) => (k === "passed") === !!r.passed).length}>
            {k[0].toUpperCase() + k.slice(1)}
          </Chip>
        ))}
        side={<Toggle label="Robot card" checked={showRobot} onChange={setShowRobot} />}
      />
      {replay ? (
        <LayersView
          world={scenario.world}
          frames={frames}
          player={player}
          showRobot={showRobot}
          onShowRobot={setShowRobot}
          agentStatus={replay.passed ? { tone: "good", label: "passed" } : { tone: "bad", label: "failed" }}
          agentHeader={<Checks replay={replay} />}
        />
      ) : (
        <Empty>{file ? "Rebuilding the run…" : "No run selected."}</Empty>
      )}
    </div>
  );
}
