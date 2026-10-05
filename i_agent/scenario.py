"""Scenario loading: turns a scenario JSON file into a ready-to-run set of layers.

Owner: Udit

A scenario file is the project's "data": the initial memory, the ground-truth world, the user
turns, and what a correct agent must do. See scenarios/README.md for the format.

Scenarios live in two sets:
  scenarios/dev/      the 10 scenarios the system was developed and tuned against
  scenarios/heldout/  10 scenarios written and frozen before the agent was ever run on them,
                      used to check that results generalise (see scenarios/heldout/FROZEN.md)
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .clock import SimClock
from .declarative import BeliefStore
from .schemas import Belief
from .sensorimotor import MockEnv
from .tools import ToolRegistry

SCENARIO_DIR = Path(__file__).resolve().parent.parent / "scenarios"
SETS = ("dev", "heldout")


@dataclass
class World:
    clock: SimClock
    store: BeliefStore
    env: MockEnv
    tools: ToolRegistry


def load_scenario(name_or_path: str) -> dict:
    """Load by file path, or by id prefix such as "A1" or "HB2" (searches dev, then heldout)."""
    p = Path(name_or_path)
    if not p.exists():
        matches = [m for s in SETS for m in sorted((SCENARIO_DIR / s).glob(f"*_{name_or_path}*.json"))]
        if not matches:
            raise FileNotFoundError(f"no scenario matching '{name_or_path}' in {SCENARIO_DIR}")
        p = matches[0]
    data = json.loads(p.read_text(encoding="utf-8"))
    data.setdefault("id", p.stem)
    data["set"] = p.parent.name
    return data


def all_scenarios(set_name: str = "dev") -> list[dict]:
    return [load_scenario(str(p)) for p in sorted((SCENARIO_DIR / set_name).glob("*.json"))]


def memory_as_text(scenario: dict) -> str:
    """The scenario's starting memory as plain text, for levels that have no memory tools."""
    return "\n".join(f"- {m['subject']}.{m['predicate']} = {m['obj']} (perspective {m.get('perspective', 'self')}, "
                     f"source {m['source']}, confidence {m.get('confidence', 1.0)}, recorded {m.get('age_s', 0)} s ago)"
                     for m in scenario.get("memory", []))


def build_world(scenario: dict, **tool_options) -> World:
    """Fresh clock, memory, world and tools for one run. tool_options go to ToolRegistry."""
    clock = SimClock()
    store = BeliefStore(clock)
    for m in scenario.get("memory", []):
        belief = Belief(subject=m["subject"], predicate=m["predicate"], obj=m["obj"],
                        perspective=m.get("perspective", "self"), source=m["source"],
                        confidence=m.get("confidence", 1.0), timestamp=clock.now() - m.get("age_s", 0))
        store.load([belief], reason=m.get("reason", "initial load"))
    env = MockEnv(scenario.get("world", {}), clock)
    return World(clock, store, env, ToolRegistry(store, env, **tool_options))
