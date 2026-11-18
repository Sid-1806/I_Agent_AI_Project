import { useId } from "react";
import { COLOURS } from "../../lib/format.js";
import { edgePoint, layoutRooms, roomsOf } from "../../lib/worldLayout.js";

// Top-down floor plan of the mock world (its ground truth).
const CELL_W = 372, CELL_H = 236, ROOM_W = 236, ROOM_H = 170, PAD = 24, CORRIDOR = 46;

const add = (a, b, k = 1) => [a[0] + b[0] * k, a[1] + b[1] * k];
const dir = (deg) => [Math.cos((deg * Math.PI) / 180), Math.sin((deg * Math.PI) / 180)];

// Geometry of the corridor for one route: door points p (from room) and q (to room).
function corridor(id, route, a, b) {
  const p = edgePoint(a, b, ROOM_W / 2, ROOM_H / 2);
  const q = edgePoint(b, a, ROOM_W / 2, ROOM_H / 2);
  const len = Math.hypot(q[0] - p[0], q[1] - p[1]) || 1;
  const u = [(q[0] - p[0]) / len, (q[1] - p[1]) / len];
  const n = [-u[1], u[0]];
  // A distance in cm along the route, as a point in the corridor.
  const at = (cm) => add(p, u, Math.max(14, Math.min(1, cm / (route.length_cm || 800)) * len));
  return { id, route, p, q, len, u, n, at, angle: (Math.atan2(u[1], u[0]) * 180) / Math.PI };
}

function Corridor({ c, planned }) {
  const half = CORRIDOR / 2;
  const w1 = [add(c.p, c.n, half), add(c.q, c.n, half)];
  const w2 = [add(c.p, c.n, -half), add(c.q, c.n, -half)];
  return (
    <g>
      <line x1={c.p[0]} y1={c.p[1]} x2={c.q[0]} y2={c.q[1]} className="corridor-floor" strokeWidth={CORRIDOR} />
      <line x1={w1[0][0]} y1={w1[0][1]} x2={w1[1][0]} y2={w1[1][1]} className="corridor-wall" />
      <line x1={w2[0][0]} y1={w2[0][1]} x2={w2[1][0]} y2={w2[1][1]} className="corridor-wall" />
      <line x1={c.p[0]} y1={c.p[1]} x2={c.q[0]} y2={c.q[1]} className={planned ? "path planned" : "path"} />
    </g>
  );
}

// Clears the wall where a corridor meets a room, so it reads as a doorway.
function Door({ point, c }) {
  const half = CORRIDOR / 2 - 4;
  const a = add(point, c.n, half);
  const b = add(point, c.n, -half);
  return <line x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} className="doorway" />;
}

function Obstacle({ c }) {
  const [x, y] = c.at(c.route.obstacle_cm);
  return (
    <g transform={`translate(${x} ${y}) rotate(${c.angle})`} className="obstacle">
      <rect x="-12" y="-17" width="24" height="34" rx="4" />
      <path d="M-12 -9 L-4 -17 M-12 1 L6 -17 M-12 11 L12 -13 M-6 17 L12 -1 M4 17 L12 9" />
      <circle cx="-8" cy="20" r="2.5" />
      <circle cx="8" cy="20" r="2.5" />
    </g>
  );
}

function ObjectIcon({ type, color }) {
  const fill = COLOURS[color] || "#777";
  switch (type) {
    case "cup":
      return (
        <g className="obj">
          <circle r="11" fill={fill} />
          <circle r="7" className="obj-inner" />
          <rect x="10" y="-3" width="6" height="6" rx="2" fill={fill} />
        </g>
      );
    case "laptop":
      return (
        <g className="obj">
          <rect x="-16" y="-11" width="32" height="22" rx="3" fill={fill} />
          <rect x="-12" y="-8" width="24" height="12" rx="1.5" className="obj-inner" />
        </g>
      );
    case "keys":
      return (
        <g className="obj">
          <circle cx="-5" r="7" fill="none" stroke={fill} strokeWidth="3" />
          <path d="M2 0 H14 M10 0 V5 M14 0 V4" stroke={fill} strokeWidth="3" fill="none" />
        </g>
      );
    case "bin":
      return (
        <g className="obj">
          <circle r="13" fill={fill} />
          <circle r="9" className="obj-inner" />
        </g>
      );
    case "chair":
      return (
        <g className="obj">
          <rect x="-12" y="-10" width="24" height="22" rx="4" fill={fill} />
          <rect x="-12" y="-15" width="24" height="6" rx="2" fill={fill} className="obj-edge" />
        </g>
      );
    default: // box, crate
      return (
        <g className="obj">
          <rect x="-14" y="-14" width="28" height="28" rx="4" fill={fill} />
          <rect x="-14" y="-3" width="28" height="6" className="obj-tape" />
          <rect x="-14" y="-14" width="28" height="9" rx="4" className="obj-light" />
        </g>
      );
  }
}

function Robot({ pos, heading, working, halo }) {
  return (
    <g className="robot" style={{ transform: `translate(${pos[0]}px, ${pos[1]}px)` }}>
      <circle r="34" fill={`url(#${halo})`} className={`robot-halo${working ? " pulse" : ""}`} />
      <g transform={`rotate(${heading})`}>
        <rect x="-13" y="-22" width="26" height="7" rx="3" className="wheel" />
        <rect x="-13" y="15" width="26" height="7" rx="3" className="wheel" />
        <circle r="18" className="robot-body" />
        <circle r="18" className="robot-rim" />
        <rect x="9" y="-7" width="10" height="14" rx="3" className="robot-sensor" />
        <circle cx="-5" cy="0" r="3.5" className="robot-led" />
      </g>
    </g>
  );
}

function LidarFan({ origin, c, reading }) {
  const hit = c.at(reading.distance_cm);
  const blocked = reading.status === "blocked";
  return (
    <g className={`lidar ${blocked ? "blocked" : "clear"}`}>
      {[-3, -2, -1, 0, 1, 2, 3].map((k) => {
        const end = add(hit, c.n, k * 7);
        return <line key={k} x1={origin[0]} y1={origin[1]} x2={end[0]} y2={end[1]} style={{ animationDelay: `${Math.abs(k) * 60}ms` }} />;
      })}
      <circle cx={hit[0]} cy={hit[1]} r="10" className="lidar-hit" />
    </g>
  );
}

function CameraView({ origin, toward, roomId }) {
  const a = (Math.atan2(toward[1] - origin[1], toward[0] - origin[0]) * 180) / Math.PI;
  const R = 230;
  const l = add(origin, dir(a - 38), R);
  const r = add(origin, dir(a + 38), R);
  return <path d={`M${origin[0]} ${origin[1]} L${l[0]} ${l[1]} A${R} ${R} 0 0 1 ${r[0]} ${r[1]} Z`} className="camera-cone" clipPath={`url(#clip-${roomId})`} />;
}

export default function WorldMap({ world, frames, frame, plannedRoute }) {
  const uid = useId().replace(/:/g, "");
  const pos = layoutRooms(world, roomsOf(world, frames));
  const xs = Object.values(pos).map((v) => v[0]);
  const ys = Object.values(pos).map((v) => v[1]);
  const minX = Math.min(...xs);
  const minY = Math.min(...ys);
  const W = (Math.max(...xs) - minX + 1) * CELL_W + PAD * 2;
  const H = (Math.max(...ys) - minY + 1) * CELL_H + PAD * 2;
  const centre = (room) => [PAD + (pos[room][0] - minX) * CELL_W + CELL_W / 2, PAD + (pos[room][1] - minY) * CELL_H + CELL_H / 2];
  const roomKey = (room) => uid + room.replace(/\W/g, "");

  const facingOf = Object.fromEntries(Object.entries(world.robot?.facing || {}).map(([d, id]) => [id, d]));
  const corridors = Object.entries(world.routes || {})
    .filter(([, r]) => r.from in pos && r.to in pos)
    .map(([id, r]) => corridor(id, r, centre(r.from), centre(r.to)));

  // The robot waits just inside the door of the route it faces; elsewhere it sits mid-room.
  const room = frame?.room || world.robot?.room;
  const door = corridors.find((c) => c.route.from === room && facingOf[c.id]);
  const robotPos = door ? add(door.p, door.u, -48) : add(centre(room), [0, 24]);
  const heading = door ? door.angle : -90;

  const data = frame?.result?.ok ? frame.result.data : null;
  const lidar = frame?.name === "read_lidar" && data?.payload?.route ? data.payload : null;
  const lidarCorridor = lidar && corridors.find((c) => c.id === lidar.route);
  const camera = frame?.name === "read_camera" && data ? data.payload : null;

  // Object positions: a row along the far side of each room.
  const objectsIn = (r) => Object.entries(world.objects || {}).filter(([, o]) => o.room === r);
  const objectPos = (r, i) => {
    const c = centre(r);
    return [c[0] - ROOM_W / 2 + 40 + i * 62, c[1] + ROOM_H / 2 - 42];
  };

  return (
    <svg className="world-map" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Floor plan of the simulated world">
      <defs>
        <pattern id={`${uid}blueprint`} width="20" height="20" patternUnits="userSpaceOnUse">
          <path d="M20 0 H0 V20" className="grid-fine" />
        </pattern>
        <pattern id={`${uid}blueprint-major`} width="100" height="100" patternUnits="userSpaceOnUse">
          <path d="M100 0 H0 V100" className="grid-major" />
        </pattern>
        <pattern id={`${uid}tiles`} width="24" height="24" patternUnits="userSpaceOnUse">
          <path d="M24 0 H0 V24" className="tile-line" />
        </pattern>
        <radialGradient id={`${uid}glow-yellow`}>
          <stop offset="0%" stopColor="#ffcf5a" stopOpacity="0.32" />
          <stop offset="100%" stopColor="#ffcf5a" stopOpacity="0" />
        </radialGradient>
        <radialGradient id={`${uid}robot-halo`}>
          <stop offset="0%" stopColor="#d4f05c" stopOpacity="0.45" />
          <stop offset="100%" stopColor="#d4f05c" stopOpacity="0" />
        </radialGradient>
        {Object.keys(pos).map((r) => {
          const c = centre(r);
          return (
            <clipPath key={r} id={`clip-${roomKey(r)}`}>
              <rect x={c[0] - ROOM_W / 2} y={c[1] - ROOM_H / 2} width={ROOM_W} height={ROOM_H} rx="10" />
            </clipPath>
          );
        })}
      </defs>
      <rect width={W} height={H} fill={`url(#${uid}blueprint)`} />
      <rect width={W} height={H} fill={`url(#${uid}blueprint-major)`} />

      {corridors.map((c) => (
        <Corridor key={c.id} c={c} planned={c.id === plannedRoute} />
      ))}

      {Object.keys(pos).map((r) => {
        const c = centre(r);
        const light = world.lighting?.[r] || "normal";
        const x0 = c[0] - ROOM_W / 2;
        const y0 = c[1] - ROOM_H / 2;
        return (
          <g key={r} className={`room light-${light}${camera?.room === r ? " seen" : ""}`}>
            <rect x={x0} y={y0} width={ROOM_W} height={ROOM_H} rx="10" className="room-floor" />
            <rect x={x0} y={y0} width={ROOM_W} height={ROOM_H} rx="10" fill={`url(#${uid}tiles)`} />
            {light === "yellow" && <circle cx={c[0]} cy={c[1]} r={ROOM_W * 0.62} fill={`url(#${uid}glow-yellow)`} clipPath={`url(#clip-${roomKey(r)})`} />}
            {light === "dim" && <rect x={x0} y={y0} width={ROOM_W} height={ROOM_H} rx="10" className="room-dim" />}
            <rect x={x0} y={y0} width={ROOM_W} height={ROOM_H} rx="10" className="room-wall" />
          </g>
        );
      })}

      {corridors.flatMap((c) => [<Door key={`${c.id}-p`} point={c.p} c={c} />, <Door key={`${c.id}-q`} point={c.q} c={c} />])}
      {corridors.filter((c) => c.route.obstacle_cm != null).map((c) => <Obstacle key={c.id} c={c} />)}

      {camera && camera.room === room && <CameraView origin={robotPos} toward={centre(room)} roomId={roomKey(room)} />}

      {Object.keys(pos).map((r) =>
        objectsIn(r).map(([id, o], i) => {
          const [x, y] = objectPos(r, i);
          const det = camera?.room === r && camera.detections.find((d) => d.object_id === id);
          return (
            <g key={id} transform={`translate(${x} ${y})`}>
              <ObjectIcon type={o.type} color={o.color} />
              <text y={det ? 40 : 30} textAnchor="middle" className="obj-label">
                {id}
              </text>
              {det && (
                <g className="detection">
                  <rect x="-24" y="-24" width="48" height="48" rx="4" />
                  <text x="-24" y="-30" className="detection-label">
                    sees {det.perceived_color}
                  </text>
                </g>
              )}
            </g>
          );
        })
      )}

      {lidarCorridor && <LidarFan origin={robotPos} c={lidarCorridor} reading={lidar} />}

      <Robot pos={robotPos} heading={heading} working={frame?.type === "tool_call"} halo={`${uid}robot-halo`} />

      {/* labels on top */}
      {Object.keys(pos).map((r) => {
        const c = centre(r);
        const light = world.lighting?.[r] || "normal";
        return (
          <g key={r} className="room-label">
            <text x={c[0] - ROOM_W / 2 + 14} y={c[1] - ROOM_H / 2 + 24}>
              {r.replace("_", " ")}
            </text>
            {light !== "normal" && (
              <g transform={`translate(${c[0] + ROOM_W / 2 - 14} ${c[1] - ROOM_H / 2 + 20})`} className={`light-tag light-${light}`}>
                <text textAnchor="end">{light} light</text>
              </g>
            )}
          </g>
        );
      })}
      {corridors.map((c) => {
        const mid = add(c.p, c.u, c.len / 2);
        const above = add(mid, c.n, -(CORRIDOR / 2 + 12));
        const below = add(mid, c.n, CORRIDOR / 2 + 20);
        const vertical = Math.abs(c.u[1]) > Math.abs(c.u[0]);
        return (
          <g key={c.id} className="corridor-label">
            <text x={vertical ? mid[0] + CORRIDOR / 2 + 10 : above[0]} y={vertical ? mid[1] - 6 : above[1]} textAnchor={vertical ? "start" : "middle"}>
              {c.id}
              {facingOf[c.id] ? ` · ${facingOf[c.id]}` : ""}
            </text>
            {c.route.obstacle_cm != null && (
              <text x={vertical ? mid[0] + CORRIDOR / 2 + 10 : below[0]} y={vertical ? mid[1] + 10 : below[1]} textAnchor={vertical ? "start" : "middle"} className="danger">
                obstacle at {c.route.obstacle_cm} cm
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
