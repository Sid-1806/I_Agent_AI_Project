export const ago = (s) =>
  s < 120 ? `${s} s` : s < 7200 ? `${Math.round(s / 60)} min` : s < 172800 ? `${Math.round(s / 3600)} h` : `${Math.round(s / 86400)} d`;

export const perspectiveClass = (p) => (p.startsWith("agent:") ? "p-agent" : `p-${p}`);

export const COLOURS = {
  red: "#c0392b", blue: "#2e5c9a", green: "#3f7d3a", brown: "#7a5230", yellow: "#d9b72c", orange: "#d9782c",
  black: "#222222", white: "#ffffff", purple: "#6a4c93", grey: "#999999", gray: "#999999", pink: "#d98aa7",
  olive: "#7b7a2e", beige: "#e3d6b4",
};

export const LIGHT = { yellow: "#f4e9b8", dim: "#dcdad3", normal: "#ffffff" };

// One line describing what a tool returned, and whether it was an error.
export function toolSummary(frame) {
  const r = frame.result || {};
  if (!r.ok) return { text: r.error || "error", error: true };
  const d = r.data || {};
  const p = d.payload || {};
  const conflicts = d.memory_check?.conflicts || [];
  const check = conflicts.length
    ? "\nmemory check: " +
      conflicts.map((c) => (c.stored_value ? `${c.perspective} says ${c.stored_value}` : `${c.subject}: ${c.observation}`)).join("; ") +
      (d.memory_check.advice ? ` · ${d.memory_check.advice}` : "")
    : "";
  switch (frame.name) {
    case "read_lidar":
      return { text: (p.route ? `${p.route}: ${p.distance_cm} cm, ${p.status}` : "no route in that direction") + check };
    case "read_camera":
      return {
        text: `${p.room}, ${p.ambient_light} light: ` + (p.detections.map((x) => `${x.object_id} ${x.perceived_color}`).join(", ") || "nothing") + check,
      };
    case "get_pose":
      return { text: `in ${p.room}` };
    case "move":
      return { text: d.success ? `now in ${d.detail.now_in}` : `${d.detail?.error}${check}` };
    case "query_beliefs": {
      let t = d.beliefs?.length ? `${d.beliefs.length} belief(s)` : d.note || "nothing";
      for (const x of d.disagreements || [])
        t += `\nrecords disagree on ${x.entity}.${x.property}: ` + x.newest_first.map((y) => `${y.value} (${y.source}, ${y.recorded})`).join(" · ");
      return { text: t };
    }
    case "get_provenance":
      return { text: d.history?.length ? `${d.history.length} log record(s)` : d.note };
    case "update_belief":
    case "record_user_belief": {
      const w = d.written;
      let t = w ? `stored ${w.entity}.${w.property} = ${w.value} [${w.perspective}, ${w.source}, ${w.confidence}]` : "";
      for (const x of d.downgraded || []) t += `\nconflict rule: ${x.perspective} ${x.value} ${x.old_confidence} → ${x.new_confidence}`;
      return { text: t };
    }
    default:
      return { text: JSON.stringify(d).slice(0, 200) };
  }
}

// What the sensorimotor layer did at this step, in one sentence.
export function sensorReadout(frame) {
  if (!frame) return "";
  if (frame.type === "start") return "Robot (R) is waiting. Squares show each object's true colour.";
  if (frame.type !== "tool_call") return "No sensor in use at this step.";
  const r = frame.result || {};
  if (!r.ok) return `${frame.name}: refused by the tool layer.\n${r.error || ""}`;
  const d = r.data || {};
  const p = d.payload || {};
  switch (frame.name) {
    case "read_lidar":
      return p.route ? `LiDAR ${p.direction}: ${p.route}, ${p.distance_cm} cm → ${p.status}` : `LiDAR ${p.direction}: no route in that direction`;
    case "read_camera":
      return (
        `Camera in ${p.room} (${p.ambient_light} light): ` +
        (p.detections.length ? p.detections.map((x) => `${x.object_id} looks ${x.perceived_color} (${x.confidence})`).join(", ") : "nothing detected")
      );
    case "get_pose":
      return `Odometry: in ${p.room}, facing ${JSON.stringify(p.facing)}`;
    case "move":
      return d.success ? `Drove: now in ${d.detail.now_in}` : `Did not move: ${d.detail?.error}`;
    default:
      return "Memory tool: the world is not touched.";
  }
}
