import { AlertTriangle, Camera, Compass, Navigation, Radar, X } from "lucide-react";
import Gauge from "./Gauge.jsx";
import { Badge } from "../ui.jsx";
import { COLOURS, describeConflict } from "../../lib/format.js";

const BLOCKED_BELOW_CM = 50;

function Warning({ children }) {
  return (
    <div className="warning">
      <AlertTriangle size={14} strokeWidth={2} />
      <span>{children}</span>
    </div>
  );
}

export const showsSensor = (frame) =>
  frame?.type === "tool_call" && ["read_lidar", "read_camera", "move", "get_pose"].includes(frame.name);

// Card beside the map: what the sensorimotor layer returned at the selected step.
export default function SensorCard({ frame, world, onClose }) {
  if (!showsSensor(frame)) return null;
  const r = frame.result || {};
  const d = r.data || {};
  const p = d.payload || {};
  const conflicts = d.memory_check?.conflicts || [];
  let icon = Radar;
  let title = "";
  let badge = null;
  let body = null;

  if (!r.ok) {
    icon = frame.name === "move" ? Navigation : Radar;
    title = frame.name === "move" ? `Drive ${frame.args?.route ?? ""}` : frame.name;
    badge = <Badge tone="bad">refused</Badge>;
    body = <Warning>{(r.error || "").replace(/^ValueError: /, "")}</Warning>;
  } else if (frame.name === "read_lidar") {
    title = `LiDAR · ${p.direction}`;
    if (!p.route) {
      badge = <Badge>no route</Badge>;
      body = <p className="sensor-note">{p.advice || p.note}</p>;
    } else {
      const length = world.routes?.[p.route]?.length_cm || 800;
      const blocked = p.status === "blocked";
      badge = (
        <Badge tone={blocked ? "bad" : "good"} dot>
          {p.status}
        </Badge>
      );
      body = (
        <>
          <div className="sensor-row">
            <span className="muted">Route</span>
            <b>{p.route}</b>
            <span className="muted">Blocked below</span>
            <b>{BLOCKED_BELOW_CM} cm</b>
          </div>
          <Gauge value={p.distance_cm} max={length} threshold={BLOCKED_BELOW_CM} unit="cm" tone={blocked ? "bad" : "good"} />
        </>
      );
    }
  } else if (frame.name === "read_camera") {
    icon = Camera;
    title = `Camera · ${p.room}`;
    badge = <Badge tone={p.ambient_light === "normal" ? "muted" : "warn"}>{p.ambient_light} light</Badge>;
    body = p.detections.length ? (
      <ul className="detections">
        {p.detections.map((det) => {
          const truth = world.objects?.[det.object_id]?.color;
          return (
            <li key={det.object_id}>
              <b>{det.object_id}</b>
              <span className="swatch-pair">
                <i style={{ background: COLOURS[det.perceived_color] }} /> seen {det.perceived_color}
              </span>
              {truth && truth !== det.perceived_color && (
                <span className="swatch-pair muted">
                  <i style={{ background: COLOURS[truth] }} /> true {truth}
                </span>
              )}
              <span className="mono muted">{det.confidence}</span>
            </li>
          );
        })}
      </ul>
    ) : (
      <p className="sensor-note">Nothing detected in {p.room}.</p>
    );
  } else if (frame.name === "move") {
    icon = Navigation;
    title = `Drive ${frame.args?.route ?? ""}`;
    badge = <Badge tone={d.success ? "good" : "bad"}>{d.success ? "arrived" : "stopped"}</Badge>;
    body = <p className="sensor-note">{d.success ? `Now in ${d.detail.now_in}.` : d.detail?.error}</p>;
  } else if (frame.name === "get_pose") {
    icon = Compass;
    title = "Odometry";
    body = (
      <div className="sensor-row">
        <span className="muted">Room</span>
        <b>{p.room}</b>
        {Object.entries(p.facing || {}).map(([dir, route]) => (
          <span key={dir} className="contents">
            <span className="muted">{dir}</span>
            <b>{route}</b>
          </span>
        ))}
      </div>
    );
  }
  const Icon = icon;
  return (
    <div className="sensor-card">
      <div className="sensor-head">
        <span className="sensor-icon">
          <Icon size={16} strokeWidth={2} />
        </span>
        <div>
          <h3>{title}</h3>
          {badge}
        </div>
        <button type="button" className="close" onClick={onClose} aria-label="Hide sensor card">
          <X size={14} />
        </button>
      </div>
      {body}
      {conflicts.length > 0 && (
        <Warning>
          Memory check: {conflicts.map(describeConflict).join("; ")}
        </Warning>
      )}
    </div>
  );
}
