import BeliefTable from "./BeliefTable.jsx";
import ProvenanceLog from "./ProvenanceLog.jsx";

export default function MemoryPanel({ frame, previous }) {
  return (
    <section className="panel">
      <h2>
        Memory <span>· declarative layer. Belief graph (NetworkX) and provenance log (SQLite).</span>
      </h2>
      <div className="panel-body">
        {frame && (
          <>
            <BeliefTable beliefs={frame.beliefs} previous={previous?.beliefs} />
            <ProvenanceLog rows={frame.provenance} previousCount={previous ? previous.provenance.length : frame.provenance.length} />
          </>
        )}
      </div>
    </section>
  );
}
