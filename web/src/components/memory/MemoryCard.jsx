import { useState } from "react";
import { Database } from "lucide-react";
import BeliefTable from "./BeliefTable.jsx";
import ProvenanceFeed from "./ProvenanceFeed.jsx";
import { Card, CardHeader, Segmented } from "../ui.jsx";

// Declarative layer: the belief graph (NetworkX) and the provenance log (SQLite).
export default function MemoryCard({ frame, previous }) {
  const [tab, setTab] = useState("beliefs");
  if (!frame) return null;
  return (
    <Card className="memory-card">
      <CardHeader icon={Database} title="Memory">
        <Segmented
          options={[
            { value: "beliefs", label: `Belief graph · ${frame.beliefs.length}` },
            { value: "log", label: `Provenance log · ${frame.provenance.length}` },
          ]}
          value={tab}
          onChange={setTab}
        />
      </CardHeader>
      <div className="memory-body">
        {tab === "beliefs" ? (
          <BeliefTable beliefs={frame.beliefs} previous={previous?.beliefs} />
        ) : (
          <ProvenanceFeed rows={frame.provenance} previousCount={previous ? previous.provenance.length : frame.provenance.length} />
        )}
      </div>
    </Card>
  );
}
