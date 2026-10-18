// Half-dial gauge, like a speedometer: value against a maximum, with a threshold tick.
export default function Gauge({ value, max, threshold, unit, tone }) {
  const R = 54;
  const cx = 70;
  const cy = 66;
  const angle = (v) => Math.PI * (1 - Math.min(1, Math.max(0, v / max)));
  const point = (v, r = R) => [cx + r * Math.cos(angle(v)), cy - r * Math.sin(angle(v))];
  const arc = (from, to) => {
    const [x1, y1] = point(from);
    const [x2, y2] = point(to);
    return `M ${x1} ${y1} A ${R} ${R} 0 0 1 ${x2} ${y2}`;
  };
  const [tx1, ty1] = point(threshold, R - 9);
  const [tx2, ty2] = point(threshold, R + 6);
  const [nx, ny] = point(value, R - 16);
  return (
    <svg className="gauge" viewBox="0 0 140 84" role="img" aria-label={`${value} ${unit}`}>
      <path d={arc(0, max)} className="gauge-track" />
      <path d={arc(0, threshold)} className="gauge-zone" />
      {value > 0 && <path d={arc(0, Math.min(value, max))} className={`gauge-value tone-stroke-${tone}`} />}
      <line x1={tx1} y1={ty1} x2={tx2} y2={ty2} className="gauge-tick" />
      <line x1={cx} y1={cy} x2={nx} y2={ny} className="gauge-needle" />
      <circle cx={cx} cy={cy} r="4" className="gauge-hub" />
      <text x={cx} y={cy + 16} textAnchor="middle" className="gauge-value-text">
        {value} {unit}
      </text>
    </svg>
  );
}
