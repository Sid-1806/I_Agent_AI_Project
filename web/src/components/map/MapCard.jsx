import WorldMap from "./WorldMap.jsx";
import RobotCard from "./RobotCard.jsx";
import { sensorState } from "../../lib/format.js";

// Sensorimotor layer: the world map with the robot's latest sensor readings beside it.
export default function MapCard({ world, frames, at, plannedRoute }) {
  const frame = frames[at];
  return (
    <section className="map-card" aria-label="World: sensorimotor layer">
      <WorldMap world={world} frames={frames} frame={frame} plannedRoute={plannedRoute} />
      <RobotCard world={world} frame={frame} sensors={sensorState(frames, at)} />
      <div className="map-foot">World · the agent never sees this map, only its sensor readings.</div>
    </section>
  );
}
