import WorldMap from "./WorldMap.jsx";
import { sensorReadout } from "../lib/format.js";

export default function WorldPanel({ world, frames, frame }) {
  return (
    <section className="panel">
      <h2>
        World <span>· sensorimotor layer. Ground truth; the agent sees it only through sensor tools.</span>
      </h2>
      <div className="panel-body">
        <WorldMap world={world} frames={frames} frame={frame} />
        <div className="readout">{sensorReadout(frame)}</div>
      </div>
    </section>
  );
}
