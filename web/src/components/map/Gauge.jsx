// Speedometer-style dial: a value against a maximum, with the threshold zone marked.
export default function Gauge({ value, max, threshold, tone, unit }) {
  const R = 50;
  const cx = 64;
  const cy = 62;
  const start = Math.PI * 1.15;
  const end = -Math.PI * 0.15;
  const angle = (v) => start + (end - start) * Math.min(1, Math.max(0, v / max));
  const point = (v, r = R) => [cx + r * Math.cos(angle(v)), cy - r * Math.sin(angle(v))];
  const arc = (from, to) => {
    const [x1, y1] = point(from);
    const [x2, y2] = point(to);
    const large = angle(from) - angle(to) > Math.PI ? 1 : 0;
    return `M ${x1} ${y1} A ${R} ${R} 0 ${large} 1 ${x2} ${y2}`;
  };
  const ticks = Array.from({ length: 21 }, (_, i) => (i / 20) * max);
  const [nx, ny] = point(value, R - 14);
  return (
    <svg className="gauge" viewBox="0 0 128 92" role="img" aria-label={`${value} ${unit}`}>
      <path d={arc(0, max)} className="gauge-track" />
      <path d={arc(0, threshold)} className="gauge-zone" />
      <path d={arc(0, Math.min(value, max))} className={`gauge-fill tone-stroke-${tone}`} />
      {ticks.map((t, i) => {
        const [x1, y1] = point(t, R - 8);
        const [x2, y2] = point(t, R - (i % 5 === 0 ? 14 : 11));
        return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} className="gauge-tick" />;
      })}
      <line x1={cx} y1={cy} x2={nx} y2={ny} className="gauge-needle" />
      <circle cx={cx} cy={cy} r="4.5" className="gauge-hub" />
      <text x={cx} y={cy + 24} textAnchor="middle" className="gauge-value">
        {value} {unit}
      </text>
    </svg>
  );
}
