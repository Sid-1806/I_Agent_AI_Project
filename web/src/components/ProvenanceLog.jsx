// The SQLite provenance log, newest first. Records written by this step are shown in full colour.
export default function ProvenanceLog({ rows, previousCount }) {
  const fresh = rows.length - previousCount;
  return (
    <div className="provenance">
      <h3>
        Provenance log (SQLite) · {rows.length} record{rows.length === 1 ? "" : "s"}, newest first
      </h3>
      {rows
        .map((r, i) => ({ r, i }))
        .reverse()
        .map(({ r, i }) => {
          const value = r.old == null || r.old === r.new ? r.new : `${r.old} → ${r.new}`;
          const conf = r.oc == null || r.oc === r.nc ? r.nc : `${r.oc} → ${r.nc}`;
          return (
            <div key={i} className={`prov${rows.length - i <= fresh ? " fresh" : ""}`}>
              {r.s}.{r.p} [{r.persp}] {value} · conf {conf} · {r.src} · {r.reason}
            </div>
          );
        })}
    </div>
  );
}
