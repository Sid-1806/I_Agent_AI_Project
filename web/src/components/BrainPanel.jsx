import { useEffect, useRef } from "react";
import TraceItem from "./TraceItem.jsx";
import AskBox from "./AskBox.jsx";

export default function BrainPanel({ frames, cursor, onSelect, live, busy, suggestions, onAsk }) {
  const body = useRef(null);
  const current = useRef(null);
  useEffect(() => {
    const box = body.current;
    const item = current.current;
    if (box && item) box.scrollTop = Math.max(0, item.offsetTop + item.offsetHeight - box.clientHeight + 12);
  }, [cursor, frames.length]);
  return (
    <section className="panel">
      <h2>
        Brain <span>· procedural layer. The LLM's steps and tool calls.</span>
      </h2>
      <div className="panel-body" ref={body}>
        <ol className="trace">
          {frames.slice(0, cursor + 1).map((f, i) => (
            <div key={i} ref={i === cursor ? current : null}>
              <TraceItem frame={f} current={i === cursor} onSelect={() => onSelect(i)} />
            </div>
          ))}
        </ol>
      </div>
      {live && <AskBox suggestions={suggestions} busy={busy} onAsk={onAsk} />}
    </section>
  );
}
