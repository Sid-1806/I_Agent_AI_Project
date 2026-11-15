import { useMemo, useState } from "react";
import { AlertTriangle, BarChart3, CheckCheck, FlaskConical, ListChecks, TrendingUp } from "lucide-react";
import StatBar from "../components/shell/StatBar.jsx";
import PageHeader from "../components/shell/PageHeader.jsx";
import BarChart from "../components/results/BarChart.jsx";
import FailureQueue from "../components/results/FailureQueue.jsx";
import RunActivity from "../components/results/RunActivity.jsx";
import { Card, CardHead, Chip, Empty, Segmented } from "../components/ui.jsx";
import { useFetch } from "../hooks.js";
import * as api from "../api.js";
import { LEVEL_LABEL, SET_LABEL, pct } from "../lib/format.js";

const SETS = ["dev", "heldout", "heldout2"];
const LEVELS = ["baseline", "sensors", "plain", "checks", "full"];
const SERIES = SETS.map((s) => ({ key: s, label: SET_LABEL[s] }));

// Evaluation results from every logged run, by system version. Versions are never pooled.
export default function ResultsPage({ config, onReplay, onError }) {
  const data = useFetch(api.getResults, onError);
  const [metric, setMetric] = useState("answer_k");
  const rows = useMemo(() => (data?.rows || []).filter((r) => r.temperature === 0), [data]);
  const versions = [...new Set(rows.map((r) => r.system))].sort();
  const [picked, setPicked] = useState(null);
  const version = picked || versions[versions.length - 1];

  if (!data) return <div className="page"><Empty>Loading results…</Empty></div>;

  const mine = rows.filter((r) => r.system === version);
  const full = mine.filter((r) => r.level === "full");
  const runs = full.reduce((a, r) => a + r.runs, 0);
  const answers = full.reduce((a, r) => a + r.answer_k, 0);
  const all = full.reduce((a, r) => a + r.all_k, 0);
  const failing = data.failing.filter((f) => f.system === version);
  const bar = (r) => ({ key: r.set, k: r[metric], n: r.runs });

  const byLevel = LEVELS.filter((lv) => mine.some((r) => r.level === lv)).map((lv) => ({
    label: LEVEL_LABEL[lv],
    bars: mine.filter((r) => r.level === lv).map(bar),
  }));
  const byVersion = versions.map((v) => ({
    label: v,
    sub: rows.find((r) => r.system === v && r.level === "full")?.model,
    bars: rows.filter((r) => r.system === v && r.level === "full").map(bar),
  }));

  return (
    <div className="page">
      <StatBar
        config={config}
        stats={[
          { icon: FlaskConical, label: "Full-system runs", value: runs },
          { icon: CheckCheck, label: "Correct answers", value: `${pct(answers, runs)}%` },
          { icon: ListChecks, label: "All checks", value: `${pct(all, runs)}%` },
          { icon: AlertTriangle, label: "Failing runs", value: failing.length },
        ]}
      />
      <PageHeader
        title="Evaluation"
        subtitle="Every logged run, temperature 0. Each system version is reported separately; held-out sets were frozen before any run on them."
        filters={versions.map((v) => (
          <Chip key={v} active={v === version} onClick={() => setPicked(v)} count={rows.filter((r) => r.system === v).reduce((a, r) => a + r.runs, 0)}>
            System {v}
          </Chip>
        ))}
        side={
          <Segmented
            label="Measure"
            value={metric}
            onChange={setMetric}
            options={[
              { value: "answer_k", label: "Correct answer", title: "Every answer check passed" },
              { value: "all_k", label: "All checks", title: "Answer, tools, memory and grounding checks all passed" },
            ]}
          />
        }
      />
      <div className="results-grid">
        <div className="results-col">
          <Card className="fill">
            <CardHead icon={AlertTriangle} title="Failing runs">
              <span className="quiet">full system · {version}</span>
            </CardHead>
            <div className="card-scroll">
              <FailureQueue items={failing} onReplay={onReplay} />
            </div>
          </Card>
          <Card className="fill">
            <CardHead icon={ListChecks} title="Recent runs" />
            <div className="card-scroll">
              <RunActivity folders={data.folders} />
            </div>
          </Card>
        </div>
        <div className="results-col">
          <Card>
            <CardHead icon={BarChart3} title="What each part adds">
              <span className="quiet">system {version}</span>
            </CardHead>
            {byLevel.length ? <BarChart groups={byLevel} series={SERIES} /> : <p className="quiet pad">No runs.</p>}
            {byLevel.length === 1 && (
              <p className="quiet chart-note">
                Only the full system has been run on {version}. Choose an earlier version to compare the safeguard levels.
              </p>
            )}
          </Card>
          <Card>
            <CardHead icon={TrendingUp} title="Full system across versions" />
            <BarChart groups={byVersion} series={SERIES} />
          </Card>
        </div>
      </div>
    </div>
  );
}
