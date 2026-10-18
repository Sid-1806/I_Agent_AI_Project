import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, Pause, Play } from "lucide-react";
import { stepKind } from "../lib/format.js";

// Step player along the bottom: one tick per step, coloured by kind. Arrow keys and space work too.
export default function Timeline({ frames, cursor, onChange }) {
  const [playing, setPlaying] = useState(false);
  const last = Math.max(0, frames.length - 1);
  const go = (i) => onChange(Math.max(0, Math.min(last, i)));

  useEffect(() => {
    if (!playing) return undefined;
    if (cursor >= last) {
      setPlaying(false);
      return undefined;
    }
    const t = setTimeout(() => go(cursor + 1), 1000);
    return () => clearTimeout(t);
  }, [playing, cursor, last]);

  useEffect(() => {
    const onKey = (e) => {
      if (["TEXTAREA", "INPUT", "SELECT"].includes(e.target.tagName)) return;
      if (e.key === "ArrowRight") go(cursor + 1);
      if (e.key === "ArrowLeft") go(cursor - 1);
      if (e.key === " ") {
        e.preventDefault();
        setPlaying((p) => !p);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const frame = frames[cursor];
  const { label } = stepKind(frame);
  return (
    <div className="timeline">
      <button
        type="button"
        className="play"
        onClick={() => {
          if (!playing && cursor >= last) go(0);
          setPlaying(!playing);
        }}
        aria-label={playing ? "Pause" : "Play"}
      >
        {playing ? <Pause size={16} /> : <Play size={16} />}
      </button>
      <button type="button" className="icon-btn" onClick={() => go(cursor - 1)} aria-label="Previous step">
        <ChevronLeft size={16} />
      </button>
      <button type="button" className="icon-btn" onClick={() => go(cursor + 1)} aria-label="Next step">
        <ChevronRight size={16} />
      </button>
      <div className="track" role="slider" aria-valuemin={0} aria-valuemax={last} aria-valuenow={cursor} aria-label="Step">
        {frames.map((f, i) => (
          <button
            key={i}
            type="button"
            className={`tick tone-bg-${stepKind(f).tone}${i === cursor ? " on" : ""}${i > cursor ? " later" : ""}`}
            onClick={() => go(i)}
            aria-label={`Step ${i}: ${stepKind(f).label}`}
            title={`#${i} ${stepKind(f).label}${f.name ? ` · ${f.name}` : ""}`}
          />
        ))}
      </div>
      <span className="timeline-label mono">
        #{cursor} / {last} · {label}
        {frame?.name ? ` · ${frame.name}` : ""}
      </span>
    </div>
  );
}
