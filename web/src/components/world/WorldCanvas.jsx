import { COLOURS } from "../../lib/format.js";
import { edgePoint, layoutRooms, roomsOf } from "../../lib/layout.js";

const CW = 330, CH = 210, BW = 178, BH = 132, PAD = 40;

function Route({ id, route, a, b, facing, lidar, moved, labels }) {
  const p = edgePoint(a, b, BW / 2, BH / 2);
  const q = edgePoint(b, a, BW / 2, BH / 2);
  const len = Math.hypot(q[0] - p[0], q[1] - p[1]);
  const ux = (q[0] - p[0]) / len;
  const uy = (q[1] - p[1]) / len;
  const at = (cm) => Math.max(10, Math.min(1, cm / (route.length_cm || 800)) * len);
  const along = (cm) => [p[0] + ux * at(cm), p[1] + uy * at(cm)];
  const scanned = lidar && lidar.route === id;
  const hit = scanned && lidar.distance_cm != null ? along(lidar.distance_cm) : null;
  const obstacle = route.obstacle_cm != null ? along(route.obstacle_cm) : null;
  const mx = (p[0] + q[0]) / 2;
  const my = (p[1] + q[1]) / 2;
  const vertical = Math.abs(uy) > Math.abs(ux);
  if (labels) {
    // Drawn after the rooms so nothing covers them.
    return (
      <g>
        <text x={vertical ? mx + 14 : mx} y={vertical ? my - 6 : my - 14} textAnchor={vertical ? "start" : "middle"} className="map-label">
          {id}
          {facing ? ` · ${facing}` : ""}
        </text>
        {route.obstacle_cm != null && (
          <text x={vertical ? mx + 14 : mx} y={vertical ? my + 10 : my + 24} textAnchor={vertical ? "start" : "middle"} className="map-label danger">
            obstacle at {route.obstacle_cm} cm
          </text>
        )}
      </g>
    );
  }
  return (
    <g>
      <line x1={p[0]} y1={p[1]} x2={q[0]} y2={q[1]} className="road" />
      <line x1={p[0]} y1={p[1]} x2={q[0]} y2={q[1]} className={`road-line${moved ? " driven" : ""}`} />
      {hit && (
        <>
          <line x1={p[0]} y1={p[1]} x2={hit[0]} y2={hit[1]} className={`beam ${lidar.status}`} />
          <circle cx={hit[0]} cy={hit[1]} r="7" className={`beam-hit ${lidar.status}`} />
        </>
      )}
      {obstacle && <rect x={obstacle[0] - 7} y={obstacle[1] - 7} width="14" height="14" rx="3" className="obstacle" />}
    </g>
  );
}

function Room({ name, c, light, objects, camera, hasRobot }) {
  const seen = camera && camera.room === name;
  const x0 = c[0] - BW / 2;
  const y0 = c[1] - BH / 2;
  let y = y0 + 40;
  return (
    <g>
      <rect x={x0} y={y0} width={BW} height={BH} rx="12" className={`room light-${light}${seen ? " seen" : ""}`} />
      <text x={x0 + 12} y={y0 + 20} className="room-name">
        {name.replace("_", " ")}
      </text>
      {light !== "normal" && (
        <text x={x0 + BW - 12} y={y0 + 20} textAnchor="end" className="map-label warn">
          {light} light
        </text>
      )}
      {objects.map(([id, o]) => {
        const det = seen && camera.detections.find((d) => d.object_id === id);
        const top = y;
        y += det ? 34 : 22;
        return (
          <g key={id}>
            <rect x={x0 + 12} y={top} width="14" height="14" rx="3" fill={COLOURS[o.color] || "#888"} className="object" />
            <text x={x0 + 32} y={top + 11} className="map-label strong">
              {id}
            </text>
            {det && (
              <text x={x0 + 32} y={top + 26} className="map-label accent">
                camera: {det.perceived_color}
              </text>
            )}
          </g>
        );
      })}
      {hasRobot && (
        <g transform={`translate(${c[0] + BW / 2 - 26} ${c[1] + BH / 2 - 26})`}>
          <circle r="22" className="robot-halo" />
          <circle r="13" className="robot" />
          <text y="4" textAnchor="middle" className="robot-label">
            R
          </text>
        </g>
      )}
    </g>
  );
}

// Ground truth of the mock world, drawn like a map, with the sensor of the selected step on top.
export default function WorldCanvas({ world, frames, frame, zoom }) {
  const pos = layoutRooms(world, roomsOf(world, frames));
  const xs = Object.values(pos).map((v) => v[0]);
  const ys = Object.values(pos).map((v) => v[1]);
  const minX = Math.min(...xs);
  const minY = Math.min(...ys);
  const W = (Math.max(...xs) - minX + 1) * CW + PAD * 2;
  const H = (Math.max(...ys) - minY + 1) * CH + PAD * 2;
  const centre = (room) => [PAD + (pos[room][0] - minX) * CW + CW / 2, PAD + (pos[room][1] - minY) * CH + CH / 2];
  const data = frame?.result?.ok ? frame.result.data : null;
  const lidar = frame?.name === "read_lidar" && data ? data.payload : null;
  const camera = frame?.name === "read_camera" && data ? data.payload : null;
  const moved = frame?.name === "move" && data?.success ? frame.args?.route : null;
  const facing = Object.fromEntries(Object.entries(world.robot?.facing || {}).map(([d, id]) => [id, d]));
  const routes = Object.entries(world.routes || {}).filter(([, r]) => r.from in pos && r.to in pos);
  // Zoom keeps the centre fixed.
  const vw = W / zoom;
  const vh = H / zoom;
  const viewBox = `${(W - vw) / 2} ${(H - vh) / 2} ${vw} ${vh}`;
  return (
    <svg className="world-canvas" viewBox={viewBox} preserveAspectRatio="xMidYMid meet" role="img" aria-label="World map">
      <defs>
        <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">
          <path d="M 24 0 L 0 0 0 24" className="grid-line" />
        </pattern>
        <radialGradient id="halo">
          <stop offset="0%" stopColor="#c6f35a" stopOpacity="0.45" />
          <stop offset="100%" stopColor="#c6f35a" stopOpacity="0" />
        </radialGradient>
      </defs>
      <rect x={-W} y={-H} width={W * 3} height={H * 3} fill="url(#grid)" />
      {routes.map(([id, r]) => (
        <Route key={id} id={id} route={r} a={centre(r.from)} b={centre(r.to)} facing={facing[id]} lidar={lidar} moved={moved === id} />
      ))}
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
        <Route key={id} id={id} route={r} a={centre(r.from)} b={centre(r.to)} facing={facing[id]} labels />
      ))}
    </svg>
  );
}
