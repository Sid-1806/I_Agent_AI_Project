import MapCard from "../components/map/MapCard.jsx";
import MemoryCard from "../components/memory/MemoryCard.jsx";
import AgentCard from "../components/agent/AgentCard.jsx";
import Timeline from "../components/Timeline.jsx";

// The three layers side by side at the selected step: world (map), memory, and the agent's steps.
export default function LayersView({ world, frames, player, showRobot, onShowRobot, agentStatus, agentHeader, composer }) {
  const at = player.at;
  const frame = frames[at];
  const planned = frame?.beliefs.find((b) => b.s === "robot" && b.p === "planned_route")?.o;
  return (
    <>
      <div className="layers">
        <div className="layers-left">
          <MapCard world={world} frames={frames} at={at} plannedRoute={planned} showRobot={showRobot} onShowRobot={onShowRobot} />
          <MemoryCard frame={frame} previous={at > 0 ? frames[at - 1] : null} />
        </div>
        <AgentCard frames={frames} at={at} onSelect={player.go} status={agentStatus} header={agentHeader} composer={composer} />
      </div>
      <Timeline frames={frames} player={player} />
    </>
  );
}

export function stepStats(frames, at) {
  const shown = frames.slice(0, at + 1);
  const frame = frames[at];
  return {
    tools: shown.filter((f) => f.type === "tool_call").length,
    checks: shown.filter((f) => f.type === "self_check").length,
    refused: shown.filter((f) => f.type === "tool_call" && !f.result?.ok).length,
    beliefs: frame?.beliefs.length ?? 0,
    records: frame?.provenance.length ?? 0,
  };
}
