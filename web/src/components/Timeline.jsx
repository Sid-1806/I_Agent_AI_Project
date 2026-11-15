import { ChevronLeft, ChevronRight, Pause, Play } from "lucide-react";
import { stepKind } from "../lib/format.js";

// Step player: one segment per step, coloured by kind. Click a segment, use the arrows, or play.
export default function Timeline({ frames, player }) {
  const { at, playing, togglePlay, go } = player;
  const frame = frames[at];
  return (
    <div className="timeline">
      <button type="button" className="play" onClick={togglePlay} aria-label={playing ? "Pause" : "Play"}>
        {playing ? <Pause size={16} /> : <Play size={16} />}
      </button>
      <button type="button" className="icon-btn" onClick={() => go(at - 1)} aria-label="Previous step">
        <ChevronLeft size={16} />
      </button>
      <button type="button" className="icon-btn" onClick={() => go(at + 1)} aria-label="Next step">
        <ChevronRight size={16} />
      </button>
      <div className="track">
        {frames.map((f, i) => {
          const { label, tone } = stepKind(f);
          return (
            <button
              key={i}
              type="button"
              className={`seg tone-bg-${tone}${i === at ? " on" : ""}${i > at ? " later" : ""}`}
              onClick={() => go(i)}
              aria-label={`Step ${i}: ${label}${f.name ? ` ${f.name}` : ""}`}
              title={`#${i} ${label}${f.name ? ` · ${f.name}` : ""}`}
            />
          );
        })}
      </div>
      <span className="timeline-label mono">
        #{at} / {frames.length - 1} · {stepKind(frame).label}
        {frame?.name ? ` · ${frame.name}` : ""}
      </span>
    </div>
  );
}
