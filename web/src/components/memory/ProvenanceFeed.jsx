import { ArrowRight } from "lucide-react";
import { perspectiveKind } from "../../lib/format.js";

// The SQLite provenance log, newest first. Records written by the selected step are marked.
export default function ProvenanceFeed({ rows, previousCount }) {
  const fresh = rows.length - previousCount;
  const list = rows.map((r, i) => ({ r, i })).reverse();
  return (
    <ol className="prov-feed">
      {list.map(({ r, i }) => {
        const isFresh = rows.length - i <= fresh;
        const valueChanged = r.old != null && r.old !== r.new;
        const confChanged = r.oc != null && r.oc !== r.nc;
        return (
          <li key={i} className={isFresh ? "fresh" : ""}>
            <div className="prov-head">
              <span className="mono strong">
                {r.s}.{r.p}
              </span>
              <span className={`persp persp-${perspectiveKind(r.persp)}`}>{r.persp}</span>
              <span className="mono muted prov-id">#{i + 1}</span>
            </div>
            <div className="prov-change mono">
              {valueChanged ? (
                <>
                  {r.old} <ArrowRight size={11} /> {r.new}
                </>
              ) : (
                r.new
              )}
              <span className="muted">
                {" "}
                · conf{" "}
                {confChanged ? (
                  <>
                    {r.oc} <ArrowRight size={11} /> {r.nc}
                  </>
                ) : (
                  r.nc
                )}
              </span>
            </div>
            <div className="prov-reason">
              <span className="mono muted">{r.src}</span> · {r.reason}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
