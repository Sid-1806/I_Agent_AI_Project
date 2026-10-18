import { ago, perspectiveClass } from "../lib/format.js";

const key = (b) => `${b.s}|${b.p}|${b.persp}`;

// The belief graph: one row per edge (entity, property, perspective). Rows changed by this step
// are marked, with the old value or confidence shown.
export default function BeliefTable({ beliefs, previous }) {
  const before = Object.fromEntries((previous || []).map((b) => [key(b), b]));
  const rows = [...beliefs].sort((a, b) => key(a).localeCompare(key(b)));
  let last = null;
  return (
    <table className="beliefs">
      <thead>
        <tr>
          <th>entity</th>
          <th>property</th>
          <th>value</th>
          <th>perspective · source</th>
          <th>confidence</th>
          <th>age</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((b) => {
          const old = before[key(b)];
          const changed = previous && (!old || old.o !== b.o || old.conf !== b.conf);
          const entity = b.s === last ? "" : b.s;
          last = b.s;
          return (
            <tr key={key(b)} className={changed ? "changed" : ""}>
              <td className="mono strong">{entity}</td>
              <td>{b.p}</td>
              <td>{old && old.o !== b.o ? `${old.o} → ${b.o}` : b.o}</td>
              <td>
                <span className={`persp ${perspectiveClass(b.persp)}`}>{b.persp}</span>
                <div className="src">{b.src}</div>
              </td>
              <td className="mono nowrap">
                {old && old.conf !== b.conf && `${old.conf} → `}
                <span className="bar">
                  <i style={{ width: `${Math.round(b.conf * 100)}%` }} />
                </span>
                {b.conf}
              </td>
              <td className="mono nowrap">{ago(b.age)}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
