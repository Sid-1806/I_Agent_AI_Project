import { COLOURS, LIGHT } from "../lib/format.js";
import { edgePoint, layoutRooms, roomsOf } from "../lib/layout.js";

const CW = 300, CH = 170, BW = 150, BH = 120, PAD = 24;
const MARK = "#b85c00";

function Route({ id, route, a, b, facing, lidar }) {
  const p = edgePoint(a, b, BW / 2, BH / 2);
  const q = edgePoint(b, a, BW / 2, BH / 2);
  const len = Math.hypot(q[0] - p[0], q[1] - p[1]);
  const ux = (q[0] - p[0]) / len;
  const uy = (q[1] - p[1]) / len;
  const at = (cm) => Math.max(8, Math.min(1, cm / (route.length_cm || 800)) * len);
  const scanned = lidar && lidar.route === id;
  const mx = (p[0] + q[0]) / 2;
  const my = (p[1] + q[1]) / 2;
  const obstacle = route.obstacle_cm != null ? [p[0] + ux * at(route.obstacle_cm), p[1] + uy * at(route.obstacle_cm)] : null;
  const hit = scanned && lidar.distance_cm != null ? [p[0] + ux * at(lidar.distance_cm), p[1] + uy * at(lidar.distance_cm)] : null;
  return (
    <g>
      <line x1={p[0]} y1={p[1]} x2={q[0]} y2={q[1]} stroke="#1c1c1a" strokeWidth={scanned ? 3 : 1.5} />
      {obstacle && <rect x={obstacle[0] - 5} y={obstacle[1] - 5} width="10" height="10" fill="#1c1c1a" />}
      {hit && (
        <>
          <line x1={p[0]} y1={p[1]} x2={hit[0]} y2={hit[1]} stroke={MARK} strokeWidth="3" strokeDasharray="5 3" />
          <circle cx={hit[0]} cy={hit[1]} r="4" fill="none" stroke={MARK} strokeWidth="2" />
        </>
      )}
      <text x={mx} y={my - 8} textAnchor="middle">
        {id}
        {facing ? ` (${facing})` : ""}
      </text>
      {route.obstacle_cm != null && (
        <text x={mx} y={my + 20} textAnchor="middle">
          obstacle {route.obstacle_cm} cm
        </text>
      )}
    </g>
  );
}

function Room({ name, c, light, objects, camera, hasRobot }) {
  const seen = camera && camera.room === name;
  let y = c[1] - BH / 2 + (light !== "normal" ? 40 : 26);
  const x = c[0] - BW / 2 + 8;
  return (
    <g>
      <rect x={c[0] - BW / 2} y={c[1] - BH / 2} width={BW} height={BH} fill={LIGHT[light] || "#fff"} stroke={seen ? MARK : "#1c1c1a"} strokeWidth={seen ? 3 : 1} />
      <text x={c[0] - BW / 2 + 6} y={c[1] - BH / 2 + 16} fontWeight="600">
        {name}
      </text>
      {light !== "normal" && (
        <text x={c[0] - BW / 2 + 6} y={c[1] - BH / 2 + 31} style={{ fill: "#6a6a64" }}>
          {light} light
        </text>
      )}
      {objects.map(([id, o]) => {
        const det = seen && camera.detections.find((d) => d.object_id === id);
        const top = y;
        y += det ? 35 : 20;
        return (
          <g key={id}>
            <rect x={x} y={top} width="14" height="14" fill={COLOURS[o.color] || "#ccc"} stroke="#1c1c1a" />
            <text x={x + 20} y={top + 11}>
              {id} {o.color}
            </text>
            {det && (
              <text x={x + 20} y={top + 26} style={{ fill: MARK }}>
                camera: {det.perceived_color}
              </text>
            )}
          </g>
        );
      })}
      {hasRobot && (
        <g>
          <circle cx={c[0] + BW / 2 - 18} cy={c[1] + BH / 2 - 18} r="10" fill="#1c1c1a" />
          <text x={c[0] + BW / 2 - 18} y={c[1] + BH / 2 - 14} textAnchor="middle" style={{ fill: "#fff" }} fontWeight="600">
            R
          </text>
        </g>
      )}
    </g>
  );
}

// Ground truth of the mock environment, with the sensor used at the current step drawn on top.
export default function WorldMap({ world, frames, frame }) {
  const pos = layoutRooms(world, roomsOf(world, frames));
  const xs = Object.values(pos).map((p) => p[0]);
  const ys = Object.values(pos).map((p) => p[1]);
  const minX = Math.min(...xs);
  const minY = Math.min(...ys);
  const W = (Math.max(...xs) - minX + 1) * CW + PAD;
  const H = (Math.max(...ys) - minY + 1) * CH + PAD;
  const centre = (room) => [PAD / 2 + (pos[room][0] - minX) * CW + CW / 2, PAD / 2 + (pos[room][1] - minY) * CH + CH / 2];
  const data = frame?.result?.ok ? frame.result.data : null;
  const lidar = frame?.name === "read_lidar" && data ? data.payload : null;
  const camera = frame?.name === "read_camera" && data ? data.payload : null;
  const facing = Object.fromEntries(Object.entries(world.robot?.facing || {}).map(([d, id]) => [id, d]));
  const routes = Object.entries(world.routes || {}).filter(([, r]) => r.from in pos && r.to in pos);
  return (
    <svg className="world" viewBox={`0 0 ${W} ${H}`} style={{ maxWidth: W * 1.15 }} role="img" aria-label="World map">
      {Object.keys(pos).map((room) => (
        <Room
          key={room}
          name={room}
          c={centre(room)}
          light={world.lighting?.[room] || "normal"}
          objects={Object.entries(world.objects || {}).filter(([, o]) => o.room === room)}
          camera={camera}
          hasRobot={frame?.room === room}
        />
      ))}
      {routes.map(([id, r]) => (
        <Route key={id} id={id} route={r} a={centre(r.from)} b={centre(r.to)} facing={facing[id]} lidar={lidar} />
      ))}
    </svg>
  );
}
