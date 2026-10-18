"""Tool registry: the only doorway between the LLM and the other two layers.

Owner: Rudraksh

Each tool is a plain Python function plus an OpenAI-style JSON schema. The LLM sees only the
schemas; execute() runs the function and always returns a JSON ToolResult string, even on
errors, so the loop never crashes on a bad call.

Memory check: every sensor reading is cross-referenced against the belief graph. Disagreements
are attached to the tool result ("memory_check") and kept in open_conflicts until the agent
resolves them with update_belief. The LLM still decides what to do; the registry only makes the
contradiction impossible to overlook.

Ablation switches (all on by default) let the evaluation measure what each safeguard adds:
  memory_check     cross-check sensor readings against memory and track open conflicts
  grounded_writes  refuse to write values that never appeared in a tool result
  disagreement_summary  list disagreeing records newest first in query_beliefs
  allowed_tools    expose only some tools (e.g. sensors only, for the "sensors" level)
Argument repair and error messages stay on at every level: they fix formatting, not reasoning.
"""
from __future__ import annotations

import inspect
import json
from typing import Any, Callable

from .declarative import BeliefStore, source_kind
from .schemas import MAP, SELF, USER, Belief, ToolResult
from .sensorimotor import MockEnv


def _fn(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "properties": properties, "required": required}}}


_STR = {"type": "string"}

# Tool parameters use plain words (entity / property / value) because small models misread the
# graph terms subject / predicate / object. These are other names models use for the same thing.
ARG_ALIASES = {
    "entity": ("subject", "object", "item", "item_id", "object_id", "entity_id", "name", "target"),
    "property": ("predicate", "attribute", "relation", "key", "field"),
    "value": ("obj", "new_value", "state", "status"),
}

WRITE_TOOLS = ("update_belief", "record_user_belief")
NEGATIVE_VALUES = ("not", "unknown", "absent", "missing", "no_")

_ENTITY = {**_STR, "description": "The thing the belief is about, e.g. 'route_A' or 'box_01'"}
_PROPERTY = {**_STR, "description": "Which property of it, e.g. 'status', 'color', 'located_at'"}

TOOL_SCHEMAS = [
    _fn("query_beliefs",
        "MEMORY (declarative layer). Look up stored beliefs. Both filters are optional; call with no "
        "arguments to list everything you know. Results always include every perspective: 'self' "
        "(your own belief), 'map' (static baseline map), 'user' (what the user believes), "
        "'agent:<id>' (a report logged by another robot). age_s = seconds since it was recorded. "
        "To see where a belief came from, use get_provenance.",
        {"entity": _ENTITY, "property": _PROPERTY},
        []),
    _fn("get_provenance",
        "MEMORY (declarative layer). Full change history for an entity from the provenance log: "
        "every old and new value, its source, confidence, time and reason.",
        {"entity": _ENTITY, "property": _PROPERTY},
        ["entity"]),
    _fn("update_belief",
        "MEMORY (declarative layer). Write YOUR OWN ('self') belief, e.g. after a sensor reading. "
        "If it contradicts the static map, the map's confidence is automatically downgraded. "
        "Only use values you actually observed in a tool result.",
        {"entity": _ENTITY, "property": _PROPERTY,
         "value": {**_STR, "description": "New value, e.g. 'blocked'"},
         "source": {**_STR, "description": "Sensor or record it came from, e.g. 'lidar_front', 'camera'"},
         "confidence": {"type": "number", "description": "0.0 to 1.0"},
         "reason": {**_STR, "description": "One sentence explaining the update"}},
        ["entity", "property", "value", "source", "confidence", "reason"]),
    _fn("record_user_belief",
        "MEMORY (declarative layer). Record what the USER believes or assumes, as stated in their "
        "message, e.g. that box_01 is red. This does not change your own beliefs.",
        {"entity": _ENTITY, "property": _PROPERTY, "value": _STR,
         "evidence": {**_STR, "description": "The user's words this is based on"}},
        ["entity", "property", "value", "evidence"]),
    _fn("read_lidar",
        "SENSOR (sensorimotor layer). Live LiDAR distance scan in a direction relative to the robot. "
        "status is 'blocked' if something is closer than 50 cm.",
        {"direction": {**_STR, "enum": ["front", "left", "right", "back"]}},
        ["direction"]),
    _fn("read_camera",
        "SENSOR (sensorimotor layer). Live camera detections in the robot's current room, with the "
        "perceived colour of each object and the ambient light level.",
        {"camera": {**_STR, "enum": ["front"], "description": "Optional; the robot has one front camera"}}, []),
    _fn("get_pose",
        "SENSOR (sensorimotor layer). Current room of the robot and which route lies in each direction.",
        {}, []),
    _fn("move",
        "ACTION (sensorimotor layer). Drive along a route to the next room. Fails if the route is blocked.",
        {"route": {**_STR, "description": "Route id, e.g. 'route_A'"}},
        ["route"]),
]


def _ago(seconds: float) -> str:
    seconds = int(seconds)
    if seconds < 120:
        return f"{seconds} s ago"
    if seconds < 7200:
        return f"{seconds // 60} min ago"
    if seconds < 172800:
        return f"{seconds // 3600} h ago"
    return f"{seconds // 86400} days ago"


class ToolRegistry:
    def __init__(self, store: BeliefStore, env: MockEnv, memory_check: bool = True,
                 grounded_writes: bool = True, disagreement_summary: bool = True,
                 allowed_tools: list[str] | None = None):
        self.store = store
        self.env = env
        self.memory_check = memory_check
        self.grounded_writes = grounded_writes
        self.disagreement_summary = disagreement_summary
        self._impl: dict[str, Callable[..., Any]] = {
            "query_beliefs": self.query_beliefs,
            "get_provenance": self.get_provenance,
            "update_belief": self.update_belief,
            "record_user_belief": self.record_user_belief,
            "read_lidar": self.read_lidar,
            "read_camera": self.read_camera,
            "get_pose": lambda: self.env.get_pose().model_dump(),
            "move": self.move,
        }
        self.schemas = TOOL_SCHEMAS
        if allowed_tools is not None:
            self._impl = {k: v for k, v in self._impl.items() if k in allowed_tools}
            self.schemas = [t for t in TOOL_SCHEMAS if t["function"]["name"] in allowed_tools]
        # (subject, predicate) -> conflict between a live reading and a stored map/self belief
        self.open_conflicts: dict[tuple[str, str], dict] = {}
        self._last_lidar: dict[str, str] = {}
        # Everything the agent has been shown by a read tool. update_belief may only write values
        # that appear here, so an invented fact can never enter memory.
        self._observed = ""
        # Entities a sensor actually measured or detected in this conversation.
        self._sensed: set[str] = set()
        # (entity, property, perspective) of every stored belief a tool result has shown the agent,
        # and the disagreements query_beliefs reported. The self-check uses both.
        self.shown: set[tuple[str, str, str]] = set()
        self.shown_disagreements: dict[tuple[str, str], dict] = {}

    @property
    def names(self) -> list[str]:
        return list(self._impl)

    def execute(self, name: str, arguments: str | dict | None) -> str:
        try:
            if name not in self._impl:
                raise ValueError(f"unknown tool '{name}'. Available: {', '.join(self.names)}")
            args = arguments if isinstance(arguments, dict) else json.loads(arguments or "{}")
            args = {k: v for k, v in args.items() if v not in (None, "")}
            args, ignored = self._normalise_args(name, args)
            data = self._impl[name](**args)
            if ignored and isinstance(data, dict):
                data["ignored_arguments"] = ignored
            result = ToolResult(ok=True, data=data)
            if name not in WRITE_TOOLS:
                self._observed += " " + json.dumps(data).lower()
        except TypeError as e:
            params = ", ".join(inspect.signature(self._impl[name]).parameters)
            result = ToolResult(ok=False, error=f"bad arguments for {name}: {e}. Expected parameters: {params}")
        except Exception as e:  # noqa: BLE001 - errors go back to the LLM, never crash the loop
            result = ToolResult(ok=False, error=f"{type(e).__name__}: {e}")
        return result.model_dump_json()

    def _normalise_args(self, name: str, args: dict) -> tuple[dict, list[str]]:
        """Map aliases onto the real parameter names and drop arguments the tool lacks.

        For the entity, an argument whose value is a known entity wins over one that is not, so
        {"object": "box_01", "subject": "located_at"} resolves to entity = box_01.
        """
        params = set(inspect.signature(self._impl[name]).parameters)
        out = {k: v for k, v in args.items() if k in params}
        used = set(out)
        entities = set(self.store.subjects()) | set(self.env.objects) | set(self.env.routes)
        for real, aliases in ARG_ALIASES.items():
            if real not in params:
                continue
            candidates = ([real] if real in out else []) + [a for a in aliases if a in args and a not in params]
            if not candidates:
                continue
            if real == "entity":
                known = [c for c in candidates if str(out.get(c, args.get(c))) in entities]
                chosen = known[0] if known else candidates[0]
            else:
                chosen = candidates[0]
            out[real] = out.get(chosen, args.get(chosen))
            used.add(chosen)
        return out, sorted(k for k in args if k not in used)

    # ------------------------------------------------------------ memory tools
    def _with_age(self, b: Belief) -> dict:
        return {"entity": b.subject, "property": b.predicate, "value": b.obj, "perspective": b.perspective,
                "source": b.source, "confidence": b.confidence,
                "age_s": round(self.store.clock.now() - b.timestamp)}

    def query_beliefs(self, entity: str = None, property: str = None, perspective: str = None):
        # The perspective filter is deliberately ignored: the LLM must always see every
        # perspective side by side, or it cannot notice that the map disagrees with itself.
        note = None
        entities = self.store.subjects()
        if entity and entity not in entities and entity in {b.predicate for b in self.store.query()}:
            entity, property = None, entity
            note = f"'{property}' is a property, so it was used as the property filter."
        rows = [self._with_age(b) for b in self.store.query(entity, property)]
        if not rows and entity in entities and property:
            rows = [self._with_age(b) for b in self.store.query(entity)]
            note = f"No '{property}' beliefs about {entity}; showing everything known about {entity}."
        if not rows:
            return {"beliefs": [], "note": "No matching beliefs in memory. You have no record of this.",
                    "known_entities": entities}
        rows.sort(key=lambda r: (r["entity"], r["property"], r["age_s"]))
        self.shown |= {(r["entity"], r["property"], r["perspective"]) for r in rows}
        out: dict = {"beliefs": rows}
        disagreements = self._disagreements(rows) if self.disagreement_summary else []
        if disagreements:
            out["disagreements"] = disagreements
            for d in disagreements:
                self.shown_disagreements[(d["entity"], d["property"])] = d
        if note:
            out["note"] = note
        return out

    @staticmethod
    def _disagreements(rows: list[dict]) -> list[dict]:
        """Where records hold different values for the same fact, list them newest first.

        The user's beliefs are left out: what the user thinks is not evidence about the world.
        """
        groups: dict[tuple[str, str], list[dict]] = {}
        for r in rows:
            if r["perspective"] == USER:
                continue
            groups.setdefault((r["entity"], r["property"]), []).append(r)
        out = []
        for (entity, prop), group in groups.items():
            if len({r["value"] for r in group}) < 2:
                continue
            ordered = sorted(group, key=lambda r: r["age_s"])
            out.append({"entity": entity, "property": prop,
                        "newest_first": [{"value": r["value"], "perspective": r["perspective"],
                                          "source": r["source"], "recorded": _ago(r["age_s"])} for r in ordered],
                        "newest": f"{ordered[0]['value']} from {ordered[0]['source']} ({_ago(ordered[0]['age_s'])})"})
        return out

    def get_provenance(self, entity: str, property: str = None):
        now = self.store.clock.now()
        rows = []
        for r in self.store.get_provenance(entity, property):
            rows.append({"entity": r.subject, "property": r.predicate, "perspective": r.perspective,
                         "old_value": r.old_obj, "new_value": r.new_obj, "old_confidence": r.old_confidence,
                         "new_confidence": r.new_confidence, "source": r.source, "reason": r.reason,
                         "age_s": round(now - r.timestamp)})
        if not rows:
            return {"history": [], "note": f"No provenance records for '{entity}'."}
        self.shown |= {(r["entity"], r["property"], r["perspective"]) for r in rows}
        return {"history": rows}

    def update_belief(self, entity: str, property: str, value: str, source: str,
                      confidence: float, reason: str):
        v = str(value).strip().lower()
        known_properties = {b.predicate for b in self.store.query()}
        if entity in known_properties and entity not in self.store.subjects():
            raise ValueError(f"'{entity}' is a property, not an entity. entity must be the thing the "
                             f"belief is about, e.g. one of {self.store.subjects()}; property is e.g. '{entity}'.")
        if self.grounded_writes:
            if v not in self._observed and not v.startswith(NEGATIVE_VALUES):
                raise ValueError(f"'{value}' does not appear in any memory record or sensor reading you have "
                                 f"seen, so it cannot be written to memory. update_belief records only what you "
                                 f"observed. Check the source again, or say that you do not know.")
            if entity not in self._sensed and entity not in self.store.subjects():
                raise ValueError(f"No sensor reading or memory record mentions '{entity}', so nothing about it "
                                 f"can be written. Values seen on other objects do not apply to it. If you have "
                                 f"no information about {entity}, say that you do not know.")
            if source_kind(source) != "sensor":
                raise ValueError(f"update_belief stores YOUR OWN sensor observations, and '{source}' is not one "
                                 f"of your sensors (lidar, camera, bumper, odometry). Reports from other robots, "
                                 f"the map and the user are already stored under their own perspective: report "
                                 f"them in your answer with their source and age instead of copying them.")
        belief = Belief(subject=entity, predicate=property, obj=str(value), perspective=SELF,
                        source=source, confidence=float(confidence), timestamp=self.store.clock.now())
        self.open_conflicts.pop((entity, property), None)
        return self._summary(self.store.assert_belief(belief, reason=reason))

    def record_user_belief(self, entity: str, property: str, value: str, evidence: str):
        belief = Belief(subject=entity, predicate=property, obj=str(value), perspective=USER,
                        source="user_utterance", confidence=1.0, timestamp=self.store.clock.now())
        return self._summary(self.store.assert_belief(belief, reason=f"user said: {evidence}"))

    def _summary(self, change: dict) -> dict:
        written = change["written"]
        if written:
            self.shown.add((written["subject"], written["predicate"], written["perspective"]))
        self.shown |= {(d["subject"], d["predicate"], d["perspective"]) for d in change["downgraded"]}
        def plain(b):
            return None if b is None else {"entity": b["subject"], "property": b["predicate"], "value": b["obj"],
                                           "perspective": b["perspective"], "source": b["source"],
                                           "confidence": b["confidence"]}
        return {"written": plain(change["written"]), "replaced": plain(change["replaced"]),
                "downgraded": [{"entity": d["subject"], "property": d["predicate"], "perspective": d["perspective"],
                                "value": d["value"], "old_confidence": d["old_confidence"],
                                "new_confidence": d["new_confidence"]} for d in change["downgraded"]]}

    # ------------------------------------------------------------ sensor tools
    def _conflicts_with(self, subject: str, predicate: str, observed: str) -> list[dict]:
        return [{"perspective": b.perspective, "stored_value": b.obj, "source": b.source,
                 "confidence": b.confidence, "age_s": round(self.store.clock.now() - b.timestamp)}
                for b in self.store.query(subject, predicate) if b.obj != observed]

    def _track(self, subject: str, predicate: str, observed: str, conflicts: list[dict],
               confirmed: bool, sensor: str) -> None:
        actionable = [c for c in conflicts if c["perspective"] in (MAP, SELF)]
        if actionable:
            self.open_conflicts[(subject, predicate)] = {
                "subject": subject, "predicate": predicate, "observed": observed, "sensor": sensor,
                "confirmed": confirmed, "conflicts": actionable}
        else:
            self.open_conflicts.pop((subject, predicate), None)

    def read_lidar(self, direction: str = "front"):
        reading = self.env.read_lidar(direction).model_dump()
        route, status = reading["payload"].get("route"), reading["payload"]["status"]
        if route is not None:
            self._sensed.add(route)
        if route is None or not self.memory_check:
            return reading
        confirmed = self._last_lidar.get(route) == status
        self._last_lidar[route] = status
        conflicts = self._conflicts_with(route, "status", status)
        self._track(route, "status", status, conflicts, confirmed, reading["sensor"])
        if conflicts:
            advice = ("Confirmed by consecutive readings. Update your own belief with update_belief."
                      if confirmed else
                      "Single reading: read once more to confirm before updating your belief.")
            reading["memory_check"] = {"conflicts": conflicts, "advice": advice}
        else:
            reading["memory_check"] = {"conflicts": [], "advice": "Reading agrees with memory."}
        return reading

    def read_camera(self, camera: str = "front"):
        reading = self.env.read_camera().model_dump()
        payload = reading["payload"]
        room, light = payload["room"], payload["ambient_light"]
        seen = {d["object_id"]: d for d in payload["detections"]}
        self._sensed |= set(seen) | {room}
        payload["note"] = (f"The camera sees only {room}, the room you are in. Objects not listed in "
                           f"detections are not in view, and their colours are unknown to the camera.")
        if not self.memory_check:
            return reading
        found = []
        # Objects memory places in this room that the camera cannot see.
        for b in self.store.query(predicate="located_at"):
            if b.obj == room and b.subject not in seen:
                c = self._conflicts_with(b.subject, "located_at", f"not_in_{room}")
                self._track(b.subject, "located_at", f"not_in_{room}", c, True, "camera")
                found.append({"subject": b.subject, "predicate": "located_at",
                              "observation": f"not visible in {room}", "conflicts": c})
        # Colours that differ from memory.
        for obj_id, det in seen.items():
            c = self._conflicts_with(obj_id, "color", det["perceived_color"])
            if c:
                note = (f"ambient light is {light}: perceived colour may be distorted"
                        if light != "normal" else "")
                if light == "normal":
                    self._track(obj_id, "color", det["perceived_color"], c, True, "camera")
                found.append({"subject": obj_id, "predicate": "color",
                              "observation": det["perceived_color"], "conflicts": c, "note": note})
        reading["memory_check"] = {"conflicts": found} if found else {
            "conflicts": [], "advice": "Detections agree with memory."}
        return reading

    def move(self, route: str):
        result = self.env.move(route).model_dump()
        self._sensed.add(route)
        if self.memory_check and "bumper" in result["detail"].get("error", ""):
            conflicts = self._conflicts_with(route, "status", "blocked")
            self._track(route, "status", "blocked", conflicts, True, "bumper")
            result["memory_check"] = {"conflicts": conflicts} if conflicts else {
                "conflicts": [], "advice": "Bumper hit agrees with memory."}
        return result

    def unverified_map_entities(self, answer: str, trace: list[dict]) -> list[dict]:
        """Entities named in the answer whose only knowledge is the static map, unchecked by any sensor this turn."""
        text = answer.lower()
        sensed = set()  # entities a sensor actually measured this turn
        for step in trace:
            if step["type"] != "tool_call" or not step["result"].get("ok"):
                continue
            data = step["result"]["data"] or {}
            payload = data.get("payload", {})
            if step["name"] == "read_lidar" and payload.get("route"):
                sensed.add(payload["route"])
            elif step["name"] == "read_camera":
                sensed |= {d["object_id"] for d in payload.get("detections", [])}
                sensed |= {b.subject for b in self.store.query(predicate="located_at")
                           if b.obj == payload.get("room")}
            elif step["name"] == "move" and isinstance(step["arguments"], dict):
                sensed.add(step["arguments"].get("route"))
        facing = {route: d for d, route in self.env.robot["facing"].items()}
        out = []
        for b in self.store.query(perspective=MAP):
            if b.subject.lower() not in text or b.subject in sensed:
                continue
            if b.predicate == "status" and b.subject in facing:
                how = f"Scan it with read_lidar(direction=\"{facing[b.subject]}\")"
            elif b.predicate == "located_at" and b.obj == self.env.robot["room"]:
                how = "Look with read_camera"
            else:
                continue  # no sensor can reach it from here, so the map is the best available evidence
            out.append({"subject": b.subject, "predicate": b.predicate, "value": b.obj,
                        "age_s": round(self.store.clock.now() - b.timestamp), "how_to_check": how})
        return out

    def actionable_conflicts(self) -> list[dict]:
        return list(self.open_conflicts.values())
