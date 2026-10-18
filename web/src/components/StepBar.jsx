import { useEffect, useState } from "react";

// Moves through the steps: buttons, slider, arrow keys and space to play.
export default function StepBar({ count, cursor, onChange }) {
  const [playing, setPlaying] = useState(false);
  const last = Math.max(0, count - 1);
  const go = (i) => onChange(Math.max(0, Math.min(last, i)));

  useEffect(() => {
    if (!playing) return undefined;
    if (cursor >= last) {
      setPlaying(false);
      return undefined;
    }
    const t = setTimeout(() => go(cursor + 1), 1100);
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

  return (
    <div className="stepbar">
      <button type="button" onClick={() => go(0)} title="First step">
        |&lt;
      </button>
      <button type="button" onClick={() => go(cursor - 1)} title="Previous step (←)">
        &lt;
      </button>
      <button
        type="button"
        onClick={() => {
          if (!playing && cursor >= last) go(0);
          setPlaying(!playing);
        }}
        title="Play (space)"
      >
        {playing ? "pause" : "play"}
      </button>
      <button type="button" onClick={() => go(cursor + 1)} title="Next step (→)">
        &gt;
      </button>
      <button type="button" onClick={() => go(last)} title="Latest step">
        &gt;|
      </button>
      <input type="range" min="0" max={last} value={cursor} onChange={(e) => go(+e.target.value)} aria-label="Step" />
      <span className="mono muted">
        step {cursor} / {last}
      </span>
    </div>
  );
}
