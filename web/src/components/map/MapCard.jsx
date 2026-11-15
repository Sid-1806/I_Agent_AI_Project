import { useState } from "react";
import { Bot, Maximize2, ZoomIn, ZoomOut } from "lucide-react";
import WorldMap from "./WorldMap.jsx";
import RobotCard from "./RobotCard.jsx";
import Compass from "./Compass.jsx";
import { IconButton } from "../ui.jsx";
import { sensorState } from "../../lib/format.js";

// Sensorimotor layer: the world map with the robot card over it.
export default function MapCard({ world, frames, at, plannedRoute, showRobot, onShowRobot }) {
  const [zoom, setZoom] = useState(1);
  const frame = frames[at];
  const sensors = sensorState(frames, at);
  return (
    <section className="map-card" aria-label="World: sensorimotor layer">
      <WorldMap world={world} frames={frames} frame={frame} plannedRoute={plannedRoute} zoom={zoom} />
      {showRobot ? (
        <RobotCard world={world} frame={frame} sensors={sensors} plannedRoute={plannedRoute} onClose={() => onShowRobot(false)} />
      ) : (
        <button type="button" className="robot-reopen" onClick={() => onShowRobot(true)}>
          <Bot size={15} /> Robot status
        </button>
      )}
      <Compass direction={sensors.lidar?.payload.direction} />
      <div className="map-controls">
        <IconButton icon={ZoomIn} label="Zoom in" onClick={() => setZoom((z) => Math.min(2.5, z * 1.25))} />
        <IconButton icon={ZoomOut} label="Zoom out" onClick={() => setZoom((z) => Math.max(0.6, z / 1.25))} />
        <IconButton icon={Maximize2} label="Fit to view" onClick={() => setZoom(1)} />
      </div>
      <div className="map-foot">
        <span>World · sensorimotor layer. The agent never sees this map, only its sensor readings.</span>
        <span>Lime road: planned route</span>
      </div>
    </section>
  );
}
