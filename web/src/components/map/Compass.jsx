const ANGLE = { front: 0, right: 90, back: 180, left: 270 };

// Dial in the map corner: which way the last LiDAR scan pointed, relative to the robot.
export default function Compass({ direction }) {
  const angle = ANGLE[direction] ?? null;
  const ticks = Array.from({ length: 48 }, (_, i) => i * 7.5);
  return (
    <div className="compass" aria-label={direction ? `Last scan: ${direction}` : "No scan yet"}>
      <svg viewBox="0 0 120 120">
        <circle cx="60" cy="60" r="56" className="compass-ring" />
        {ticks.map((a) => (
          <line
            key={a}
            x1="60"
            y1={a % 90 === 0 ? 8 : 10}
            x2="60"
            y2={a % 90 === 0 ? 18 : 14}
            transform={`rotate(${a} 60 60)`}
            className={a % 90 === 0 ? "compass-tick major" : "compass-tick"}
          />
        ))}
        {[
          ["F", 60, 30],
          ["R", 91, 64],
          ["B", 60, 97],
          ["L", 29, 64],
        ].map(([t, x, y]) => (
          <text key={t} x={x} y={y} textAnchor="middle" className="compass-letter">
            {t}
          </text>
        ))}
        <circle cx="60" cy="60" r="24" className="compass-face" />
        {angle != null && <path d="M60 22 L66 40 L54 40 Z" transform={`rotate(${angle} 60 60)`} className="compass-needle" />}
        <text x="60" y="64" textAnchor="middle" className="compass-label">
          {direction ? direction.toUpperCase() : "–"}
        </text>
      </svg>
    </div>
  );
}
