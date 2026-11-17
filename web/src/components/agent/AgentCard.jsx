import { useEffect, useRef } from "react";
import { BrainCircuit } from "lucide-react";
import FeedItem from "./FeedItem.jsx";
import Composer from "./Composer.jsx";
import { Badge, Card, CardHead } from "../ui.jsx";

// Procedural layer: the agent's steps, newest at the bottom.
export default function AgentCard({ frames, at, onSelect, status, header, composer }) {
  const list = useRef(null);
  const current = useRef(null);
  useEffect(() => {
    const box = list.current;
    const item = current.current;
    if (box && item) box.scrollTop = Math.max(0, item.offsetTop + item.offsetHeight - box.clientHeight + 16);
  }, [at, frames.length]);
  return (
    <Card className="agent-card">
      <CardHead icon={BrainCircuit} title="Agent">
        {status && <Badge tone={status.tone} dot>{status.label}</Badge>}
      </CardHead>
      {header}
      <ol className="feed" ref={list} aria-label="Agent steps">
        {frames.slice(0, at + 1).map((f, i) => (
          <div key={i} ref={i === at ? current : null}>
            <FeedItem frame={f} current={i === at} onSelect={() => onSelect(i)} />
          </div>
        ))}
      </ol>
      {composer && <Composer {...composer} />}
    </Card>
  );
}
