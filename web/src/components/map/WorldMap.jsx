import { COLOURS } from "../../lib/format.js";
import { edgePoint, layoutRooms, roomsOf } from "../../lib/worldLayout.js";

const CW = 340, CH = 220, BW = 184, BH = 136, PAD = 48;

function Road({ route, a, b, planned, beam }) {
  const p = edgePoint(a, b, BW / 2, BH / 2);
  const q = edgePoint(b, a, BW / 2, BH / 2);
  const len = Math.hypot(q[0] - p[0], q[1] - p[1]) || 1;
  const along = (cm) => {
    const d = Math.max(12, Math.min(1, cm / (route.length_cm || 800)) * len);
    return [p[0] + ((q[0] - p[0]) / len) * d, p[1] + ((q[1] - p[1]) / len) * d];
  };
  const obstacle = route.obstacle_cm != null ? along(route.obstacle_cm) : null;
  const hit = beam ? along(beam.distance_cm) : null;
  return (
    <g>
      <line x1={p[0]} y1={p[1]} x2={q[0]} y2={q[1]} className="road" />
      <line x1={p[0]} y1={p[1]} x2={q[0]} y2={q[1]} className={planned ? "road-route" : "road-centre"} />
      {obstacle && <rect x={obstacle[0] - 8} y={obstacle[1] - 8} width="16" height="16" rx="4" className="obstacle" />}
      {hit && (
        <g className={`beam ${beam.status}`}>
          <line x1={p[0]} y1={p[1]} x2={hit[0]} y2={hit[1]} />
          <circle cx={hit[0]} cy={hit[1]} r="9" />
        </g>
      )}
    </g>
  );
}

function RoadLabel({ id, route, a, b, facing }) {
  const vertical = Math.abs(b[1] - a[1]) > Math.abs(b[0] - a[0]);
  const mx = (a[0] + b[0]) / 2;
  const my = (a[1] + b[1]) / 2;
  const x = vertical ? mx + 16 : mx;
  return (
    <g className="road-label">
      <text x={x} y={vertical ? my - 4 : my - 18} textAnchor={vertical ? "start" : "middle"}>
        {id}
        {facing ? ` · ${facing}` : ""}
      </text>
      {route.obstacle_cm != null && (
        <text x={x} y={vertical ? my + 12 : my + 30} textAnchor={vertical ? "start" : "middle"} className="danger">
          obstacle at {route.obstacle_cm} cm
        </text>
      )}
    </g>
  );
}

function Room({ name, c, light, objects, seenBy, robotHere }) {
  const x0 = c[0] - BW / 2;
  const y0 = c[1] - BH / 2;
  let y = y0 + (light !== "normal" ? 46 : 36);
  return (
    <g>
      <rect x={x0} y={y0} width={BW} height={BH} rx="14" className={`room light-${light}${seenBy ? " seen" : ""}`} />
      <text x={x0 + 14} y={y0 + 22} className="room-name">
        {name.replace("_", " ")}
      </text>
      {light !== "normal" && (
        <text x={x0 + 14} y={y0 + 38} className="room-light">
          {light} light
        </text>
      )}
      {objects.map(([id, o]) => {
        const det = seenBy?.detections.find((d) => d.object_id === id);
        const top = y;
        y += det ? 34 : 22;
        return (
          <g key={id}>
            <rect x={x0 + 14} y={top} width="14" height="14" rx="4" fill={COLOURS[o.color] || "#777"} className="object" />
            <text x={x0 + 34} y={top + 11} className="object-label">
              {id}
            </text>
            {det && (
              <text x={x0 + 34} y={top + 26} className="object-seen">
                camera: {det.perceived_color}
              </text>
            )}
          </g>
        );
      })}
      {robotHere && (
        <g transform={`translate(${c[0] + BW / 2 - 34} ${c[1] + BH / 2 - 30})`} className="robot">
          <circle r="26" className="robot-halo" />
          <rect x="-15" y="-11" width="30" height="22" rx="6" className="robot-body" />
          <circle cx="-6" cy="0" r="2.6" className="robot-eye" />
          <circle cx="6" cy="0" r="2.6" className="robot-eye" />
        </g>
      )}
    </g>
  );
}

// The mock world's ground truth, drawn as a dark map. The robot's planned route is the lime road;
// the LiDAR beam and the room the camera saw show the sensor in use at the selected step.
export default function WorldMap({ world, frames, frame, plannedRoute, zoom }) {
  const pos = layoutRooms(world, roomsOf(world, frames));
  const xs = Object.values(pos).map((v) => v[0]);
  const ys = Object.values(pos).map((v) => v[1]);
  const minX = Math.min(...xs);
  const minY = Math.min(...ys);
  const W = (Math.max(...xs) - minX + 1) * CW + PAD * 2;
  const H = (Math.max(...ys) - minY + 1) * CH + PAD * 2;
  const centre = (room) => [PAD + (pos[room][0] - minX) * CW + CW / 2, PAD + (pos[room][1] - minY) * CH + CH / 2];
  const data = frame?.result?.ok ? frame.result.data : null;
  const lidar = frame?.name === "read_lidar" && data?.payload?.route ? data.payload : null;
  const camera = frame?.name === "read_camera" && data ? data.payload : null;
  const facing = Object.fromEntries(Object.entries(world.robot?.facing || {}).map(([d, id]) => [id, d]));
  const roads = Object.entries(world.routes || {}).filter(([, r]) => r.from in pos && r.to in pos);
  const vw = W / zoom;
  const vh = H / zoom;
  return (
    <svg className="world-map" viewBox={`${(W - vw) / 2} ${(H - vh) / 2} ${vw} ${vh}`} role="img" aria-label="Map of the simulated world">
      <defs>
        <pattern id="streets" width="64" height="64" patternUnits="userSpaceOnUse" patternTransform="rotate(18)">
          <path d="M0 32 H64 M32 0 V64" className="street" />
        </pattern>
        <pattern id="blocks" width="16" height="16" patternUnits="userSpaceOnUse">
          <path d="M16 0 L0 0 0 16" className="street-fine" />
        </pattern>
        <radialGradient id="halo">
          <stop offset="0%" stopColor="#d4f05c" stopOpacity="0.5" />
          <stop offset="100%" stopColor="#d4f05c" stopOpacity="0" />
        </radialGradient>
      </defs>
      <rect x={-W} y={-H} width={W * 3} height={H * 3} fill="url(#blocks)" />
      <rect x={-W} y={-H} width={W * 3} height={H * 3} fill="url(#streets)" />
      {roads.map(([id, r]) => (
        <Road key={id} route={r} a={centre(r.from)} b={centre(r.to)} planned={id === plannedRoute} beam={lidar?.route === id ? lidar : null} />
      ))}
      {Object.keys(pos).map((room) => (
        <Room
          key={room}
          name={room}
          c={centre(room)}
          light={world.lighting?.[room] || "normal"}
          objects={Object.entries(world.objects || {}).filter(([, o]) => o.room === room)}
          seenBy={camera?.room === room ? camera : null}
          robotHere={frame?.room === room}
        />
      ))}
      {roads.map(([id, r]) => (
        <RoadLabel key={id} id={id} route={r} a={centre(r.from)} b={centre(r.to)} facing={facing[id]} />
      ))}
    </svg>
  );
}
