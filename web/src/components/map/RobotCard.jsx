import { AlertTriangle, ArrowRight, Bot, Camera, Clock, Radar, X } from "lucide-react";
import Gauge from "./Gauge.jsx";
import { Badge } from "../ui.jsx";
import { COLOURS, ago, describeConflict } from "../../lib/format.js";

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

// Floating status card for the robot, like a vehicle card: where it is, its route, the last
// LiDAR and camera readings, and any warning. Tiles light up when the selected step used them.
export default function RobotCard({ world, frame, sensors, plannedRoute, onClose }) {
  const routeId = sensors.lidar?.payload.route || plannedRoute || Object.values(world.robot?.facing || {})[0];
  const route = world.routes?.[routeId];
  const lidar = sensors.lidar?.payload;
  const blocked = lidar?.status === "blocked";
  const camera = sensors.camera?.payload;
  const conflicts = [sensors.lidar, sensors.camera]
    .filter((s) => s && s.frame === frame)
    .flatMap((s) => (s.memory_check?.conflicts || []).map(describeConflict));
  const refusal = sensors.refusal && sensors.refusal.frame === frame ? sensors.refusal.frame.result.error.replace(/^ValueError: /, "") : null;
  const status = blocked ? ["blocked", "bad"] : frame?.type === "tool_call" ? ["working", "warn"] : ["idle", "good"];
  const scanned = lidar ? Math.min(100, Math.round((100 * lidar.distance_cm) / (route?.length_cm || 800))) : 0;
  return (
    <div className="robot-card">
      <div className="robot-card-head">
        <span className="robot-icon">
          <Bot size={18} strokeWidth={2} />
        </span>
        <div className="robot-title">
          <h3>
            Robot <Badge tone={status[1]} dot>{status[0]}</Badge>
          </h3>
          <span className="robot-sub">
            in {frame?.room?.replace("_", " ")} · t = {frame?.clock?.toLocaleString("en-US")} s
          </span>
        </div>
        <button type="button" className="robot-close" onClick={onClose} aria-label="Hide robot card">
          <X size={15} />
        </button>
      </div>

      {route && (
        <div className="route-box">
          <div className="route-line">
            <span>
              {route.from.replace("_", " ")} <ArrowRight size={13} /> {route.to.replace("_", " ")}
            </span>
            <span className="mono">
              {route.length_cm} cm <b>{lidar ? `${scanned}%` : "–"}</b>
            </span>
          </div>
          <div className={`route-bar${blocked ? " blocked" : ""}`}>
            <i style={{ width: `${lidar ? Math.max(scanned, 2) : 0}%` }} />
          </div>
          <div className="route-meta">
            <Clock size={12} /> {lidar ? `clear for ${lidar.distance_cm} cm along ${lidar.route}` : `${routeId} not scanned yet`}
          </div>
        </div>
      )}

      <div className="tiles">
        <Tile
          icon={Radar}
          title="LiDAR"
          live={frame?.name === "read_lidar"}
          badge={lidar && <Badge tone={blocked ? "bad" : "good"}>{lidar.status}</Badge>}
        >
          {lidar ? (
            <Gauge value={lidar.distance_cm} max={Math.min(route?.length_cm || 800, 400)} threshold={BLOCKED_BELOW_CM} tone={blocked ? "bad" : "good"} unit="cm" />
          ) : (
            <p className="tile-empty">No scan yet</p>
          )}
        </Tile>
        <Tile
          icon={Camera}
          title="Camera"
          live={frame?.name === "read_camera"}
          badge={camera && <Badge tone={camera.ambient_light === "normal" ? "muted" : "warn"}>{camera.ambient_light}</Badge>}
        >
          {camera ? (
            camera.detections.length ? (
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
                          {truth && truth !== d.perceived_color ? ` · really ${truth}` : ""}
                        </small>
                      </span>
                    </li>
                  );
                })}
              </ul>
            ) : (
              <p className="tile-empty">Nothing in view in {camera.room.replace("_", " ")}</p>
            )
          ) : (
            <p className="tile-empty">Not used yet</p>
          )}
        </Tile>
      </div>

      {refusal && (
        <div className="warning-strip bad">
          <AlertTriangle size={14} />
          <span>
            <b>Refused by the tool layer.</b> {refusal}
          </span>
        </div>
      )}
      {conflicts.length > 0 && (
        <div className="warning-strip">
          <AlertTriangle size={14} />
          <span>
            <b>Memory check:</b> {conflicts.join("; ")}
          </span>
        </div>
      )}
      {sensors.lidar && !conflicts.length && !refusal && (
        <div className="robot-foot mono">last scan {ago(Math.max(0, Math.round((frame?.clock ?? 0) - sensors.lidar.frame.result.data.t)))} ago</div>
      )}
    </div>
  );
}
