"""Tier 3: the Sensorimotor layer (mock environment).

Owner: Udit

A small simulated building. It knows the *ground truth* (where obstacles and objects really
are) and only reveals it through noisy, condition-dependent sensors. The agent never reads
the ground truth directly.

World config (from a scenario file):
{
  "robot":   {"room": "Room_101", "facing": {"front": "route_A"}},
  "routes":  {"route_A": {"from": "Room_101", "to": "Room_102", "length_cm": 800, "obstacle_cm": 12}},
  "objects": {"box_01": {"type": "box", "room": "Room_101", "color": "blue"}},
  "lighting": {"Room_101": "yellow"},
  "lidar_script": {"route_A": [9, 240, 245]}     # optional: scripted readings to simulate noise
}
"""
from __future__ import annotations

import copy
from typing import Any, Optional

from .clock import SimClock
from .schemas import ActionResult, SensorReading

BLOCKED_BELOW_CM = 50
DEFAULT_ROUTE_LENGTH_CM = 800

# How ambient light shifts the colour the camera reports.
LIGHTING_SHIFT = {
    "normal": {},
    "yellow": {"blue": "brown", "red": "orange", "white": "yellow", "green": "olive", "grey": "beige"},
    "dim": {"blue": "black", "red": "maroon", "green": "dark green", "white": "grey"},
}


class MockEnv:
    def __init__(self, world: dict[str, Any], clock: Optional[SimClock] = None):
        self.world = copy.deepcopy(world)
        self.clock = clock or SimClock()
        self.robot = self.world.setdefault("robot", {"room": "Room_101", "facing": {}})
        self.robot.setdefault("facing", {})
        self.routes = self.world.setdefault("routes", {})
        self.objects = self.world.setdefault("objects", {})
        self.lighting = self.world.setdefault("lighting", {})
        self._lidar_script = {k: list(v) for k, v in self.world.get("lidar_script", {}).items()}
        self.action_log: list[dict] = []

    # ---------------------------------------------------------------- sensors
    def read_lidar(self, direction: str = "front") -> SensorReading:
        t = self.clock.tick(1)
        route_id = self.robot["facing"].get(direction)
        if route_id is None or route_id not in self.routes:
            payload = {"direction": direction, "route": None, "distance_cm": None,
                       "status": "no_route",
                       "note": f"no route in direction '{direction}'. This is not an obstacle reading.",
                       "routes_by_direction": dict(self.robot["facing"])}
        else:
            route = self.routes[route_id]
            script = self._lidar_script.get(route_id)
            if script:
                distance = script.pop(0) if len(script) > 1 else script[0]
            elif route.get("obstacle_cm") is not None:
                distance = route["obstacle_cm"]
            else:
                distance = route.get("length_cm", DEFAULT_ROUTE_LENGTH_CM)
            payload = {"direction": direction, "route": route_id, "distance_cm": distance,
                       "status": "blocked" if distance < BLOCKED_BELOW_CM else "clear"}
        self._log("read_lidar", payload)
        return SensorReading(sensor=f"lidar_{direction}", t=t, payload=payload)

    def read_camera(self) -> SensorReading:
        t = self.clock.tick(1)
        room = self.robot["room"]
        light = self.lighting.get(room, "normal")
        shift = LIGHTING_SHIFT.get(light, {})
        detections = []
        for i, (obj_id, obj) in enumerate(sorted(self.objects.items())):
            if obj.get("room") != room:
                continue
            true_color = obj.get("color")
            detections.append({
                "object_id": obj_id,
                "label": obj.get("type", "object"),
                "perceived_color": shift.get(true_color, true_color),
                "bbox": [120 + 90 * i, 200, 80, 80],
                "confidence": 0.82 if light != "normal" else 0.95,
            })
        payload = {"room": room, "ambient_light": light, "detections": detections}
        self._log("read_camera", payload)
        return SensorReading(sensor="camera", t=t, payload=payload)

    def get_pose(self) -> SensorReading:
        t = self.clock.now()
        payload = {"room": self.robot["room"], "facing": dict(self.robot["facing"])}
        return SensorReading(sensor="odometry", t=t, payload=payload)

    # ------------------------------------------------------------------ motor
    def move(self, route_id: str) -> ActionResult:
        t = self.clock.tick(5)
        route = self.routes.get(route_id)
        if route is None:
            result = ActionResult(action="move", t=t, success=False, detail={"error": f"unknown route {route_id}"})
        elif route.get("from") != self.robot["room"]:
            result = ActionResult(action="move", t=t, success=False,
                                  detail={"error": f"{route_id} does not start in {self.robot['room']}"})
        elif route.get("obstacle_cm") is not None and route["obstacle_cm"] < BLOCKED_BELOW_CM:
            result = ActionResult(action="move", t=t, success=False,
                                  detail={"error": "bumper triggered: obstacle in path",
                                          "stopped_at_cm": route["obstacle_cm"]})
        else:
            self.robot["room"] = route["to"]
            result = ActionResult(action="move", t=t, success=True, detail={"now_in": route["to"]})
        self._log("move", result.model_dump())
        return result

    def _log(self, action: str, payload: dict) -> None:
        self.action_log.append({"t": self.clock.now(), "action": action, "payload": payload})
