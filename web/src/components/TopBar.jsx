import { Cpu, Database, FileText, ShieldAlert, Wrench } from "lucide-react";

function Stat({ icon: Icon, label, value }) {
  return (
    <span className="stat">
      <Icon size={13} strokeWidth={2} />
      {label}
      <b>{value}</b>
    </span>
  );
}

// Counts for the steps shown so far, and the model in use.
export default function TopBar({ frames, frame, config }) {
  const tools = frames.filter((f) => f.type === "tool_call").length;
  const checks = frames.filter((f) => f.type === "self_check").length;
  return (
    <div className="topbar">
      <div className="stats">
        <Stat icon={Wrench} label="Tool calls" value={tools} />
        <Stat icon={ShieldAlert} label="Self-checks" value={checks} />
        <Stat icon={Database} label="Beliefs" value={frame?.beliefs.length ?? 0} />
        <Stat icon={FileText} label="Log records" value={frame?.provenance.length ?? 0} />
      </div>
      <span className="model">
        <Cpu size={13} strokeWidth={2} />
        {config ? `${config.provider} · ${config.model}` : "connecting…"}
      </span>
    </div>
  );
}
