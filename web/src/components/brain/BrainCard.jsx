import { useEffect, useRef } from "react";
import { BrainCircuit } from "lucide-react";
import TraceRow from "./TraceRow.jsx";
import Composer from "./Composer.jsx";
import { Badge, Card, CardHeader } from "../ui.jsx";

function Checks({ checks, passed }) {
  const failed = checks.filter((c) => !c.passed);
  return (
    <div className={`checks ${passed ? "ok" : "fail"}`}>
      <b>
        Automatic checks: {checks.length - failed.length}/{checks.length} passed
      </b>
      {failed.map((c, i) => (
        <div key={i} className="small">
          {c.kind}: {c.name} {c.detail}
        </div>
      ))}
    </div>
  );
}

// Procedural layer: every LLM step, as it happens (live) or as logged (replay).
export default function BrainCard({ frames, cursor, onSelect, live, busy, suggestions, onAsk, replay }) {
  const list = useRef(null);
  const current = useRef(null);
  useEffect(() => {
    const box = list.current;
    const item = current.current;
    if (box && item) box.scrollTop = Math.max(0, item.offsetTop + item.offsetHeight - box.clientHeight + 16);
  }, [cursor, frames.length]);
  return (
    <Card className="brain-card">
      <CardHeader icon={BrainCircuit} title="Agent">
        {live ? (
          <Badge tone={busy ? "warn" : "good"} dot>
            {busy ? "working" : "ready"}
          </Badge>
        ) : (
          replay && <Badge tone={replay.passed ? "good" : "bad"}>{replay.passed ? "passed" : "failed"}</Badge>
        )}
        <span className="muted small">procedural layer · LLM + tools</span>
      </CardHeader>
      {replay && <Checks checks={replay.checks} passed={replay.passed} />}
      <ol className="trace" ref={list}>
        {frames.slice(0, cursor + 1).map((f, i) => (
          <div key={i} ref={i === cursor ? current : null}>
            <TraceRow frame={f} index={i} current={i === cursor} onSelect={() => onSelect(i)} />
          </div>
        ))}
      </ol>
      {live && <Composer suggestions={suggestions} busy={busy} onAsk={onAsk} />}
    </Card>
  );
}
