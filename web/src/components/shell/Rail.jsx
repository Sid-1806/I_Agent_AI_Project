import { History, Radio } from "lucide-react";

const PAGES = [
  { key: "operations", icon: Radio, label: "Talk to the agent" },
  { key: "replay", icon: History, label: "Replay a test log" },
];

export default function Rail({ page, onPage }) {
  return (
    <nav className="rail" aria-label="Screens">
      <div className="rail-logo" aria-hidden="true">
        I
      </div>
      {PAGES.map(({ key, icon: Icon, label }) => (
        <button key={key} type="button" className={`rail-btn${page === key ? " on" : ""}`} onClick={() => onPage(key)} aria-label={label} title={label} aria-current={page === key ? "page" : undefined}>
          <Icon size={18} strokeWidth={2} />
        </button>
      ))}
    </nav>
  );
}
