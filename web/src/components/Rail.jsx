import { FileClock, MessagesSquare } from "lucide-react";

const ITEMS = [
  { key: "live", icon: MessagesSquare, label: "Talk to the agent" },
  { key: "logs", icon: FileClock, label: "Test logs" },
];

// Slim navigation rail on the left.
export default function Rail({ mode, onMode }) {
  return (
    <nav className="rail" aria-label="Views">
      <div className="logo" aria-label="I, Agent">
        <span>I</span>
      </div>
      {ITEMS.map(({ key, icon: Icon, label }) => (
        <button key={key} type="button" className={`rail-btn${mode === key ? " on" : ""}`} onClick={() => onMode(key)} aria-label={label} title={label}>
          <Icon size={18} strokeWidth={2} />
        </button>
      ))}
    </nav>
  );
}
