import { ago, perspectiveKind } from "../../lib/format.js";

const key = (b) => `${b.s}|${b.p}|${b.persp}`;

// The belief graph, one row per edge. Rows changed by the selected step are marked.
export default function BeliefTable({ beliefs, previous }) {
  const before = Object.fromEntries((previous || []).map((b) => [key(b), b]));
  const rows = [...beliefs].sort((a, b) => key(a).localeCompare(key(b)));
  let last = null;
  return (
    <table className="beliefs">
      <thead>
        <tr>
          <th>Entity</th>
          <th>Property</th>
          <th>Value</th>
          <th>Perspective</th>
          <th>Confidence</th>
          <th className="right">Age</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((b) => {
          const old = before[key(b)];
          const isNew = previous && !old;
          const changed = previous && old && (old.o !== b.o || old.conf !== b.conf);
          const entity = b.s === last ? "" : b.s;
          last = b.s;
          const kind = perspectiveKind(b.persp);
          return (
            <tr key={key(b)} className={isNew ? "row-new" : changed ? "row-changed" : ""}>
              <td className="mono strong">{entity}</td>
              <td className="muted">{b.p}</td>
              <td className="strong">{old && old.o !== b.o ? <><s className="muted">{old.o}</s> {b.o}</> : b.o}</td>
              <td>
                <span className={`persp persp-${kind}`}>{b.persp}</span>
                <div className="src mono">{b.src}</div>
              </td>
              <td>
                <div className="conf">
                  <span className="conf-bar">
                    <i className={b.conf < 0.5 ? "low" : ""} style={{ width: `${Math.round(b.conf * 100)}%` }} />
                  </span>
                  <span className="mono">
                    {old && old.conf !== b.conf && <s className="muted">{old.conf}</s>} {b.conf}
                  </span>
                </div>
              </td>
              <td className="mono muted right">{ago(b.age)}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
