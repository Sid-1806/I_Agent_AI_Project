"""Snapshots of the three layers, for the web UI.

frame() captures the state of all three layers after one step of the agent: the step itself, where
the robot is, every belief in the graph and the provenance log. replay() rebuilds a logged run step
by step: it creates the scenario's world and memory and re-executes the run's tool calls in order.
The layers are deterministic, so this reproduces the state after every step without calling the LLM.
Each replayed tool result is compared with the logged one.
"""
from __future__ import annotations

import json
from pathlib import Path

from .evaluation import level_options
from .scenario import World, build_world, load_scenario


def beliefs(world: World) -> list[dict]:
    now = world.store.clock.now()
    return [{"s": b.subject, "p": b.predicate, "o": b.obj, "persp": b.perspective, "src": b.source,
             "conf": b.confidence, "age": round(now - b.timestamp)} for b in world.store.query()]


def provenance(world: World) -> list[dict]:
    rows = world.store.db.execute("SELECT * FROM provenance ORDER BY id").fetchall()
    return [{"s": r["subject"], "p": r["predicate"], "persp": r["perspective"], "old": r["old_obj"],
             "new": r["new_obj"], "oc": r["old_confidence"], "nc": r["new_confidence"], "src": r["source"],
             "reason": r["reason"]} for r in rows]


def frame(world: World, turn: int, step: dict, **extra) -> dict:
    """The step plus the state of the world and memory right after it."""
    return {"turn": turn, "type": step["type"], "name": step.get("name"), "args": step.get("arguments"),
            "text": step.get("text"), "result": step.get("result"), "room": world.env.robot["room"],
            "clock": world.store.clock.now(), "beliefs": beliefs(world), "provenance": provenance(world), **extra}


def scenario_info(scenario: dict) -> dict:
    return {"id": scenario["id"], "set": scenario.get("set", "dev"), "type": scenario.get("type"),
            "description": scenario.get("description", ""), "turns": scenario.get("turns", []),
            "world": scenario.get("world", {})}


def replay(log_path: Path) -> dict:
    log = json.loads(Path(log_path).read_text(encoding="utf-8"))
    scenario = load_scenario(log["scenario"])
    level = log.get("mode", "full")
    if level not in ("sensors", "plain", "checks", "full"):
        raise ValueError(f"level {level!r} has no tool calls to replay")
    tool_options, _ = level_options(level)
    world = build_world(scenario, **tool_options)
    frames = [frame(world, 0, {"type": "start"})]
    mismatches = 0
    for t, turn in enumerate(log["turns"], 1):
        world.tools.open_conflicts.clear()
        world.tools.scanned.clear()
        frames.append(frame(world, t, {"type": "question", "text": turn["question"]}))
        for step in turn["trace"]:
            if step["type"] != "tool_call":
                frames.append(frame(world, t, step))
                continue
            result = json.loads(world.tools.execute(step["name"], step.get("arguments") or {}))
            mismatches += result != step["result"]
            frames.append(frame(world, t, {**step, "result": result}, mismatch=result != step["result"]))
    return {"scenario": scenario_info(scenario), "level": level, "system": log.get("system", "v1"),
            "model": log.get("model"), "passed": log.get("passed"), "checks": log.get("checks", []),
            "file": Path(log_path).as_posix(), "frames": frames, "mismatches": mismatches}
