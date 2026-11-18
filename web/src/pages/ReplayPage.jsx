import { useEffect, useState } from "react";
import PageHeader from "../components/shell/PageHeader.jsx";
import LayersView from "./LayersView.jsx";
import { Empty, Select } from "../components/ui.jsx";
import { usePlayer } from "../hooks.js";
import * as api from "../api.js";
import { SET_LABEL, folderTime, scenarioTitle } from "../lib/format.js";

function Checks({ replay }) {
  const failed = replay.checks.filter((c) => !c.passed);
  return (
    <div className={`checks ${replay.passed ? "ok" : "fail"}`}>
      <b>
        Automatic checks: {replay.checks.length - failed.length} of {replay.checks.length} passed
      </b>
      {failed.map((c, i) => (
        <div key={i}>
          {c.kind}: {c.name} {c.detail}
        </div>
      ))}
    </div>
  );
}

// Step through a logged evaluation run, rebuilt by the server without calling the LLM.
export default function ReplayPage({ onError, initialFile = "", initialStep = 0 }) {
  const [runs, setRuns] = useState([]);
  const [file, setFile] = useState(initialFile);
  const [replay, setReplay] = useState(null);
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

  useEffect(() => {
    if (replay && file === initialFile && initialStep) player.go(initialStep);
  }, [replay]); // eslint-disable-line react-hooks/exhaustive-deps

  const scenario = replay?.scenario;
  const { code, name } = scenarioTitle(scenario?.id);
  const folders = [...new Set(runs.map((r) => r.folder))];

  return (
    <div className="page">
      <PageHeader
        title={scenario ? <><span className="title-code">{code}</span> {name}</> : "Replay a test log"}
        subtitle={
          scenario
            ? `${SET_LABEL[scenario.set]} · system ${replay.system} · ${replay.model}` +
              (replay.system !== replay.current_system ? ` · memory rebuilt with ${replay.current_system} rules` : "")
            : "The layers are rebuilt from the log; the LLM is not called."
        }
        controls={
          <Select value={file} onChange={setFile} label="Logged run">
            <option value="">Choose a logged run…</option>
            {folders.map((f) => (
              <optgroup key={f} label={`${folderTime(f)} · ${f.split("_").slice(1).join(" · ")}`}>
                {runs
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
      />
      {replay ? (
        <LayersView
          world={scenario.world}
          frames={frames}
          player={player}
          agentStatus={replay.passed ? { tone: "good", label: "passed" } : { tone: "bad", label: "failed" }}
          agentHeader={<Checks replay={replay} />}
        />
      ) : (
        <Empty>{file ? "Rebuilding the run…" : "No run selected."}</Empty>
      )}
    </div>
  );
}
