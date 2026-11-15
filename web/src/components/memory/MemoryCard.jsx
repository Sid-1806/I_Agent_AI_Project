import { useState } from "react";
import { ArrowRight, Database } from "lucide-react";
import { Card, CardHead, Segmented } from "../ui.jsx";
import { ago, perspectiveKind } from "../../lib/format.js";

const key = (b) => `${b.s}|${b.p}|${b.persp}`;

function Beliefs({ beliefs, previous }) {
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
          <th className="num">Age</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((b) => {
          const old = before[key(b)];
          const state = !previous ? "" : !old ? "new" : old.o !== b.o || old.conf !== b.conf ? "changed" : "";
          const entity = b.s === last ? "" : b.s;
          last = b.s;
          return (
            <tr key={key(b)} className={state && `row-${state}`}>
              <td className="mono strong">{entity}</td>
              <td className="muted">{b.p}</td>
              <td className="strong">
                {old && old.o !== b.o && <s className="muted">{old.o}</s>} {b.o}
              </td>
              <td>
                <span className={`persp persp-${perspectiveKind(b.persp)}`}>{b.persp}</span>
                <span className="src">{b.src}</span>
              </td>
              <td>
                <span className="conf">
                  <span className="conf-bar">
                    <i className={b.conf < 0.5 ? "low" : ""} style={{ width: `${Math.round(b.conf * 100)}%` }} />
                  </span>
                  <span className="mono">
                    {old && old.conf !== b.conf && <s className="muted">{old.conf}</s>} {b.conf}
                  </span>
                </span>
              </td>
              <td className="mono muted num">{ago(b.age)}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

function Provenance({ rows, previousCount }) {
  const fresh = rows.length - previousCount;
  return (
    <ol className="prov">
      {rows
        .map((r, i) => ({ r, i }))
        .reverse()
        .map(({ r, i }) => (
          <li key={i} className={rows.length - i <= fresh ? "fresh" : ""}>
            <span className="prov-id mono">#{i + 1}</span>
            <span className="prov-main">
              <span className="prov-head">
                <span className="mono strong">
                  {r.s}.{r.p}
                </span>
                <span className={`persp persp-${perspectiveKind(r.persp)}`}>{r.persp}</span>
              </span>
              <span className="prov-change mono">
                {r.old != null && r.old !== r.new ? (
                  <>
                    {r.old} <ArrowRight size={11} /> {r.new}
                  </>
                ) : (
                  r.new
                )}
                <span className="muted">
                  {" "}
                  · confidence{" "}
                  {r.oc != null && r.oc !== r.nc ? (
                    <>
                      {r.oc} <ArrowRight size={11} /> {r.nc}
                    </>
                  ) : (
                    r.nc
                  )}
                </span>
              </span>
              <span className="prov-reason">
                <span className="mono">{r.src}</span> · {r.reason}
              </span>
            </span>
          </li>
        ))}
    </ol>
  );
}

// Declarative layer: the belief graph (NetworkX) and the provenance log (SQLite) at the selected step.
export default function MemoryCard({ frame, previous }) {
  const [tab, setTab] = useState("beliefs");
  if (!frame) return null;
  return (
    <Card className="memory-card">
      <CardHead icon={Database} title="Memory">
        <Segmented
          label="Memory view"
          value={tab}
          onChange={setTab}
          options={[
            { value: "beliefs", label: `Belief graph · ${frame.beliefs.length}` },
            { value: "log", label: `Provenance log · ${frame.provenance.length}` },
          ]}
        />
      </CardHead>
      <div className="memory-body">
        {tab === "beliefs" ? (
          <Beliefs beliefs={frame.beliefs} previous={previous?.beliefs} />
        ) : (
          <Provenance rows={frame.provenance} previousCount={previous ? previous.provenance.length : frame.provenance.length} />
        )}
      </div>
    </Card>
  );
}
