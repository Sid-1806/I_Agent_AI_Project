// Grouped bar chart. groups: [{label, bars: [{key, k, n}]}]; series: [{key, label}].
export default function BarChart({ groups, series, height = 220 }) {
  const W = 560;
  const top = 18;
  const bottom = 44;
  const left = 38;
  const plot = height - top - bottom;
  const gw = (W - left - 8) / Math.max(1, groups.length);
  const bw = Math.min(30, (gw - 18) / series.length);
  const y = (v) => top + plot * (1 - v);
  return (
    <div className="chart">
      <svg viewBox={`0 0 ${W} ${height}`} role="img" aria-label="Bar chart">
        {[0, 0.25, 0.5, 0.75, 1].map((t) => (
          <g key={t}>
            <line x1={left} x2={W - 4} y1={y(t)} y2={y(t)} className="chart-grid" />
            <text x={left - 8} y={y(t) + 4} textAnchor="end" className="chart-axis">
              {t * 100}%
            </text>
          </g>
        ))}
        {groups.map((g, i) => {
          const cx = left + gw * (i + 0.5);
          const present = series.filter((s) => g.bars.some((b) => b.key === s.key));
          return (
            <g key={g.label}>
              {present.map((s, j) => {
                const bar = g.bars.find((b) => b.key === s.key);
                const v = bar.n ? bar.k / bar.n : 0;
                const x = cx - (bw * present.length) / 2 + j * bw + 2;
                return (
                  <g key={s.key}>
                    <rect x={x} y={y(v)} width={bw - 4} height={Math.max(2, plot * v)} rx="5" className={`bar series-${s.key}`}>
                      <title>
                        {g.label} · {s.label}: {bar.k}/{bar.n}
                      </title>
                    </rect>
                    <text x={x + (bw - 4) / 2} y={y(v) - 6} textAnchor="middle" className="chart-value">
                      {Math.round(v * 100)}
                    </text>
                  </g>
                );
              })}
              <text x={cx} y={height - bottom + 18} textAnchor="middle" className="chart-axis">
                {g.label}
              </text>
              {g.sub && (
                <text x={cx} y={height - bottom + 32} textAnchor="middle" className="chart-axis dim">
                  {g.sub}
                </text>
              )}
            </g>
          );
        })}
      </svg>
      <div className="legend">
        {series.map((s) => (
          <span key={s.key}>
            <i className={`series-${s.key}`} />
            {s.label}
          </span>
        ))}
      </div>
    </div>
  );
}
