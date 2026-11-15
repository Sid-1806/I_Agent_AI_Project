// Places rooms on a grid: the robot's room in the middle, each connected room in the direction its
// route leaves (front = right, back = left, left = up, right = down), other rooms in a row below.

const OFFSET = { front: [1, 0], back: [-1, 0], left: [0, -1], right: [0, 1] };

export function roomsOf(world, frames) {
  const rooms = new Set([world.robot?.room]);
  Object.values(world.routes || {}).forEach((r) => {
    rooms.add(r.from);
    rooms.add(r.to);
  });
  Object.values(world.objects || {}).forEach((o) => rooms.add(o.room));
  Object.keys(world.lighting || {}).forEach((r) => rooms.add(r));
  frames.forEach((f) => rooms.add(f.room));
  rooms.delete(undefined);
  return rooms;
}

export function layoutRooms(world, rooms) {
  const robot = world.robot || {};
  const routes = world.routes || {};
  const pos = {};
  const taken = new Set();
  const put = (room, x, y) => {
    pos[room] = [x, y];
    taken.add(`${x},${y}`);
  };
  put(robot.room, 0, 0);
  for (const [dir, id] of Object.entries(robot.facing || {})) {
    const r = routes[id];
    if (r && !(r.to in pos) && OFFSET[dir]) put(r.to, ...OFFSET[dir]);
  }
  let changed = true;
  while (changed) {
    changed = false;
    for (const r of Object.values(routes)) {
      if (!(r.from in pos) || r.to in pos) continue;
      const [x, y] = pos[r.from];
      for (const [dx, dy] of [[1, 0], [0, 1], [0, -1], [-1, 0]]) {
        if (!taken.has(`${x + dx},${y + dy}`)) {
          put(r.to, x + dx, y + dy);
          changed = true;
          break;
        }
      }
    }
  }
  const placed = Object.values(pos);
  let x = Math.min(...placed.map((p) => p[0]));
  const y = Math.max(...placed.map((p) => p[1])) + 1;
  [...rooms].filter((r) => !(r in pos)).sort().forEach((r) => put(r, x++, y));
  return pos;
}

// Where the segment from c towards `toward` leaves a box of half-size hw x hh centred on c.
export function edgePoint(c, toward, hw, hh) {
  const dx = toward[0] - c[0];
  const dy = toward[1] - c[1];
  const t = Math.min(Math.abs(dx) > 1e-9 ? hw / Math.abs(dx) : Infinity, Math.abs(dy) > 1e-9 ? hh / Math.abs(dy) : Infinity);
  return [c[0] + dx * t, c[1] + dy * t];
}
