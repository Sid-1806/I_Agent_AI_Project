import { useState } from "react";
import { Map as MapIcon, Maximize2, ZoomIn, ZoomOut } from "lucide-react";
import WorldCanvas from "./WorldCanvas.jsx";
import SensorCard, { showsSensor } from "./SensorCard.jsx";
import { Card, CardHeader, IconButton } from "../ui.jsx";

// Sensorimotor layer: the mock world as a map, with the selected step's sensor reading.
export default function WorldCard({ world, frames, frame, overlay, onOverlay }) {
  const [zoom, setZoom] = useState(1);
  return (
    <Card className="world-card">
      <CardHeader icon={MapIcon} title="World">
        <span className="muted small">sensorimotor layer · ground truth</span>
      </CardHeader>
      <div className={`map${overlay && showsSensor(frame) ? " with-card" : ""}`}>
        <WorldCanvas world={world} frames={frames} frame={frame} zoom={zoom} />
        {overlay && <SensorCard frame={frame} world={world} onClose={() => onOverlay(false)} />}
        <div className="map-controls">
          <IconButton icon={ZoomIn} label="Zoom in" onClick={() => setZoom((z) => Math.min(2.5, z * 1.25))} />
          <IconButton icon={ZoomOut} label="Zoom out" onClick={() => setZoom((z) => Math.max(0.6, z / 1.25))} />
          <IconButton icon={Maximize2} label="Fit" onClick={() => setZoom(1)} />
        </div>
        <div className="map-foot">
          <span>The agent never sees this map. It learns about the world only through its sensor tools.</span>
          <span className="mono">t = {frame?.clock?.toLocaleString("en-US") ?? "–"} s</span>
        </div>
      </div>
    </Card>
  );
}
