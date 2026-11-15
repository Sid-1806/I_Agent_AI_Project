import { BarChart3, History, Radio } from "lucide-react";

export const PAGES = [
  { key: "operations", icon: Radio, label: "Operations: talk to the agent" },
  { key: "replay", icon: History, label: "Replay: step through a test log" },
  { key: "results", icon: BarChart3, label: "Results: evaluation" },
];

// Slim navigation rail.
export default function Rail({ page, onPage }) {
  return (
    <nav className="rail" aria-label="Screens">
      <div className="rail-logo" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="18" height="18">
          <path d="M10 3h4v7h7v4h-7v7h-4v-7H3v-4h7z" fill="currentColor" />
        </svg>
      </div>
      {PAGES.map(({ key, icon: Icon, label }) => (
        <button key={key} type="button" className={`rail-btn${page === key ? " on" : ""}`} onClick={() => onPage(key)} aria-label={label} title={label} aria-current={page === key ? "page" : undefined}>
          <Icon size={18} strokeWidth={2} />
        </button>
      ))}
    </nav>
  );
}
