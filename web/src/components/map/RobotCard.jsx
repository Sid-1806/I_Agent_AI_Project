import { AlertTriangle, Bot, Camera, Radar } from "lucide-react";
import Gauge from "./Gauge.jsx";
import { Badge } from "../ui.jsx";
import { COLOURS, confidenceUpdate, describeConflict } from "../../lib/format.js";

const BLOCKED_BELOW_CM = 50;

function Tile({ icon: Icon, title, badge, live, children }) {
  return (
    <div className={`tile${live ? " live" : ""}`}>
      <div className="tile-head">
        <span>
          <Icon size={13} strokeWidth={2} /> {title}
        </span>
        {badge}
      </div>
      {children}
    </div>
  );
}

// The robot's latest LiDAR and camera readings, plus any warning from the selected step.
// A tile is outlined when the selected step used that sensor.
export default function RobotCard({ world, frame, sensors }) {
  const lidar = sensors.lidar?.payload;
  const camera = sensors.camera?.payload;
  const blocked = lidar?.status === "blocked";
  const route = world.routes?.[lidar?.route];
  const data = frame?.result?.data;
  const warnings = [
    ...(frame?.type === "tool_call" && !frame.result?.ok ? [frame.result.error.replace(/^ValueError: /, "")] : []),
    ...(data?.memory_check?.conflicts || []).map((c) => `Memory check: ${describeConflict(c)}`),
  ];
  return (
    <div className="robot-card">
      <div className="robot-head">
        <span className="robot-icon">
          <Bot size={17} strokeWidth={2} />
        </span>
        <div>
          <h3>Robot</h3>
          <span className="robot-sub">in {frame?.room?.replace("_", " ")}</span>
        </div>
      </div>
      <div className="tiles">
        <Tile icon={Radar} title="LiDAR" live={frame?.name === "read_lidar"} badge={lidar && <Badge tone={blocked ? "bad" : "good"}>{lidar.status}</Badge>}>
          {lidar ? (
            <>
              <Gauge value={lidar.distance_cm} max={Math.min(route?.length_cm || 800, 400)} threshold={BLOCKED_BELOW_CM} tone={blocked ? "bad" : "good"} unit="cm" />
              <p className="tile-note">
                {lidar.route}, {lidar.direction}
              </p>
            </>
          ) : (
            <p className="tile-empty">No scan yet</p>
          )}
        </Tile>
        <Tile icon={Camera} title="Camera" live={frame?.name === "read_camera"} badge={camera && camera.ambient_light !== "normal" && <Badge tone="warn">{camera.ambient_light} light</Badge>}>
          {!camera ? (
            <p className="tile-empty">Not used yet</p>
          ) : camera.detections.length ? (
            <ul className="seen-list">
              {camera.detections.map((d) => {
                const truth = world.objects?.[d.object_id]?.color;
                return (
                  <li key={d.object_id}>
                    <span className="swatch" style={{ background: COLOURS[d.perceived_color] }} />
                    <span>
                      <b>{d.object_id}</b>
                      <small>
                        looks {d.perceived_color}
                        {truth && truth !== d.perceived_color ? `, really ${truth}` : ""}
                      </small>
                    </span>
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="tile-empty">Nothing in view</p>
          )}
        </Tile>
      </div>
      {(data?.confidence_updates || []).map((u, i) => (
        <div key={`u${i}`} className="update-strip">
          <b>Memory updated</b> {confidenceUpdate(u)}
        </div>
      ))}
      {warnings.map((w, i) => (
        <div key={i} className="warning-strip">
          <AlertTriangle size={14} />
          <span>{w}</span>
        </div>
      ))}
    </div>
  );
}
