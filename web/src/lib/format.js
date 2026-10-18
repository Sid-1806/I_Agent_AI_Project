export const ago = (s) =>
  s < 120 ? `${s}s` : s < 7200 ? `${Math.round(s / 60)}m` : s < 172800 ? `${Math.round(s / 3600)}h` : `${Math.round(s / 86400)}d`;

export const agoLong = (s) =>
  s < 120 ? `${s} s ago` : s < 7200 ? `${Math.round(s / 60)} min ago` : s < 172800 ? `${Math.round(s / 3600)} h ago` : `${Math.round(s / 86400)} days ago`;

export const perspectiveKind = (p) => (p.startsWith("agent:") ? "agent" : p);

// "A1_route_blocked" -> {code: "A1", name: "Route blocked"}
export function scenarioTitle(id = "") {
  const [code, ...rest] = id.split("_");
  const name = rest.join(" ");
  return { code, name: name.charAt(0).toUpperCase() + name.slice(1) };
}

export const SCENARIO_TYPES = [
  { key: "all", label: "All" },
  { key: "A", label: "Sensor vs map" },
  { key: "B", label: "Perspectives" },
  { key: "grounding", label: "Unknowns" },
  { key: "provenance", label: "Provenance" },
];

export const SET_LABEL = { dev: "Dev set", heldout: "Held-out set 1", heldout2: "Held-out set 2" };

// True colours of objects, as drawn on the ground-truth map.
export const COLOURS = {
  red: "#e5484d", blue: "#3e7bfa", green: "#46a758", brown: "#8d5a33", yellow: "#f5d90a", orange: "#f76b15",
  black: "#111111", white: "#f4f4f2", purple: "#8e4ec6", grey: "#8b8d98", gray: "#8b8d98", pink: "#e93d82",
  olive: "#8a8a3a", beige: "#d8c7a0",
};

// Short label and tone for each kind of trace step.
export function stepKind(frame) {
  if (!frame) return { label: "", tone: "muted" };
  switch (frame.type) {
    case "start":
      return { label: "Start", tone: "muted" };
    case "question":
      return { label: "User", tone: "user" };
    case "tool_call":
      return { label: "Tool", tone: frame.result?.ok ? "tool" : "bad" };
    case "thought":
      return { label: "Thought", tone: "muted" };
    case "draft":
      return { label: "Draft", tone: "warn" };
    case "self_check":
      return { label: "Self-check", tone: "bad" };
    case "answer":
      return { label: "Answer", tone: "good" };
    case "error":
      return { label: "Error", tone: "bad" };
    default:
      return { label: "Note", tone: "muted" };
  }
}

// Lines describing what a tool returned, plus any memory-check conflict and whether it failed.
export function toolResult(frame) {
  const r = frame.result || {};
  if (!r.ok) return { lines: [r.error?.replace(/^ValueError: /, "") || "error"], error: true, conflicts: [] };
  const d = r.data || {};
  const p = d.payload || {};
  const conflicts = (d.memory_check?.conflicts || []).map(describeConflict);
  let lines;
  switch (frame.name) {
    case "read_lidar":
      lines = [p.route ? `${p.route}: ${p.distance_cm} cm → ${p.status}` : "no route in that direction"];
      break;
    case "read_camera":
      lines = [
        `${p.room} · ${p.ambient_light} light`,
        p.detections.length ? p.detections.map((x) => `${x.object_id} looks ${x.perceived_color}`).join(", ") : "nothing detected",
      ];
      break;
    case "get_pose":
      lines = [`in ${p.room}`];
      break;
    case "move":
      lines = [d.success ? `now in ${d.detail.now_in}` : d.detail?.error];
      break;
    case "query_beliefs":
      lines = [d.beliefs?.length ? `${d.beliefs.length} belief${d.beliefs.length === 1 ? "" : "s"} returned` : d.note || "nothing"];
      for (const x of d.disagreements || [])
        lines.push(`records disagree on ${x.entity}.${x.property}: ` + x.newest_first.map((y) => `${y.value} (${y.source}, ${y.recorded})`).join(" · "));
      break;
    case "get_provenance":
      lines = [d.history?.length ? `${d.history.length} log record${d.history.length === 1 ? "" : "s"}` : d.note];
      break;
    case "update_belief":
    case "record_user_belief": {
      const w = d.written;
      lines = w ? [`stored ${w.entity}.${w.property} = ${w.value} [${w.perspective}, ${w.confidence}]`] : [];
      for (const x of d.downgraded || []) lines.push(`conflict rule: ${x.perspective} "${x.value}" ${x.old_confidence} → ${x.new_confidence}`);
      break;
    }
    default:
      lines = [JSON.stringify(d).slice(0, 160)];
  }
  return { lines, error: false, conflicts, advice: d.memory_check?.advice };
}

// One memory-check conflict in words. LiDAR conflicts list the stored belief; camera conflicts
// carry the observation and the stored beliefs it contradicts.
export function describeConflict(c) {
  if (c.stored_value) return `${c.perspective} says ${c.stored_value} (${c.source})`;
  const stored = (c.conflicts || []).map((x) => `${x.perspective} says ${x.stored_value}`).join(", ");
  return `${c.subject}.${c.predicate}: sensor shows ${c.observation}${stored ? `, but ${stored}` : ""}${c.note ? ` (${c.note})` : ""}`;
}
