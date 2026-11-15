import { Cpu } from "lucide-react";

// Row of small stat pills along the top, plus the model in use.
export default function StatBar({ stats, config }) {
  return (
    <div className="statbar">
      <div className="stats">
        {stats.map(({ icon: Icon, label, value }) => (
          <span className="stat" key={label}>
            <Icon size={13} strokeWidth={2} />
            {label}
            <b>{value}</b>
          </span>
        ))}
      </div>
      <span className="stat model">
        <Cpu size={13} strokeWidth={2} />
        {config ? `${config.provider} · ${config.model}` : "connecting…"}
      </span>
    </div>
  );
}
