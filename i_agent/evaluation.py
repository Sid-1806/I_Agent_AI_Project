"""Automatic checks for one scenario run.

Owner: Udit

Four kinds of check, each tied to a claim the project makes:
  answer     the final answer says the right things
  tools      the agent actually consulted the layers it needed (it did not answer from nowhere)
  memory     the belief graph ends in the correct state (the agent updated its beliefs)
  grounding  no fact in the answer is missing from every tool result and user turn (no hallucination)

Expectation format (the "expect" block of a scenario file):
  "answer_mentions":     [["blocked", "obstruct"], ["map"]]   every group needs at least one match
  "answer_excludes":     ["is clear"]
  "tools_required":      ["read_lidar", "update_belief"]
  "tools_any":           [["query_beliefs", "get_provenance"]]   at least one tool from each group
  "tool_min_counts":     {"read_lidar": 2}
  "tools_forbidden":     ["move"]                    tools that must not be executed (a call the
                                                     tool layer refused has no effect and is allowed)
  "beliefs": [{"subject": "route_A", "predicate": "status", "perspective": "self",
               "value": "blocked" | "value_not": "x" | "value_contains": "101",
               "min_confidence": 0.9, "max_confidence": 0.5, "must_exist": true}]
  "grounded_vocab":      ["red", "green", ...]  words allowed in the answer only if a tool
                                                 result or the user mentioned them
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .declarative import BeliefStore
from .procedural import Agent, AgentResult, run_baseline
from .scenario import build_world, memory_as_text


@dataclass
class Check:
    kind: str
    name: str
    passed: bool
    detail: str = ""


def _stems(word: str) -> set[str]:
    """The word and the word minus one common ending, never shorter than four letters ('red' stays
    'red'; 'routes' gives route and rout; 'blocked' gives block)."""
    return {word} | {word[: -len(end)] for end in ("ing", "ed", "es", "s")
                     if word.endswith(end) and len(word) - len(end) >= 4}


def _mentions(text: str, word: str, inflect: bool = False) -> bool:
    """Whole-word match. With inflect, a plain inflection also counts ('not detect' matches 'not
    detected', 'hour' matches 'hours'); other suffixes never do, so 'red' never matches 'reduced'.
    Required phrases use inflect; forbidden phrases do not ('path is cleared' is not 'path is clear')."""
    if inflect and re.fullmatch(r"[a-z]+", word.lower()):
        # One word: compare stems, so 'blocked' also matches 'blocks' and 'blocking'.
        stems = _stems(word.lower())
        return any(_stems(w) & stems for w in re.findall(r"[a-z]+", text.lower()))
    suffix = r"(s|es|ed|ing)?" if inflect else ""
    plain = re.sub(r"[\"'`“”]", "", text.lower())  # 'is now "clear"' reads as 'is now clear'
    return re.search(r"(?<![a-z0-9])" + re.escape(word.lower()) + suffix + r"(?![a-z0-9])", plain) is not None


def run_checks(expect: dict, turns: list[AgentResult], store: BeliefStore | None,
               user_turns: list[str], extra_evidence: str = "") -> list[Check]:
    answer = turns[-1].answer
    checks: list[Check] = []

    for group in expect.get("answer_mentions", []):
        hit = [w for w in group if _mentions(answer, w, inflect=True)]
        checks.append(Check("answer", f"mentions one of {group}", bool(hit), f"found {hit}" if hit else ""))
    for phrase in expect.get("answer_excludes", []):
        checks.append(Check("answer", f"does not say '{phrase}'", not _mentions(answer, phrase)))

    called = [name for t in turns for name in t.tools_called]
    for tool in expect.get("tools_required", []):
        checks.append(Check("tools", f"called {tool}", tool in called))
    for group in expect.get("tools_any", []):
        hit = [t for t in group if t in called]
        checks.append(Check("tools", f"called one of {group}", bool(hit), f"called {hit}" if hit else ""))
    executed = [s["name"] for t in turns for s in t.trace
                if s["type"] == "tool_call" and s.get("result", {}).get("ok")]
    for tool in expect.get("tools_forbidden", []):
        checks.append(Check("tools", f"did not execute {tool}", tool not in executed,
                            f"executed {executed.count(tool)}x" if tool in executed else ""))
    for tool, n in expect.get("tool_min_counts", {}).items():
        count = called.count(tool)
        checks.append(Check("tools", f"called {tool} at least {n}x", count >= n, f"called {count}x"))

    for spec in expect.get("beliefs", []):
        label = f"{spec['subject']}.{spec['predicate']} [{spec['perspective']}]"
        b = store.get(spec["subject"], spec["predicate"], spec["perspective"]) if store else None
        if b is None:
            ok = not spec.get("must_exist", "value" in spec or "value_contains" in spec
                              or "min_confidence" in spec or "max_confidence" in spec)
            checks.append(Check("memory", f"{label} state", ok, "belief missing"))
            continue
        problems = []
        if "value" in spec and b.obj.lower() != spec["value"].lower():
            problems.append(f"value {b.obj!r} != {spec['value']!r}")
        if "value_not" in spec and b.obj.lower() == spec["value_not"].lower():
            problems.append(f"value is still {b.obj!r}")
        if "value_contains" in spec and spec["value_contains"].lower() not in b.obj.lower():
            problems.append(f"value {b.obj!r} lacks {spec['value_contains']!r}")
        if "min_confidence" in spec and b.confidence < spec["min_confidence"]:
            problems.append(f"confidence {b.confidence} < {spec['min_confidence']}")
        if "max_confidence" in spec and b.confidence > spec["max_confidence"]:
            problems.append(f"confidence {b.confidence} > {spec['max_confidence']}")
        checks.append(Check("memory", f"{label} state", not problems,
                            "; ".join(problems) or f"= {b.obj} (conf {b.confidence})"))

    vocab = expect.get("grounded_vocab", [])
    if vocab:
        evidence = extra_evidence + " " + " ".join(user_turns) + " " + " ".join(
            json.dumps(s.get("result", "")) for t in turns for s in t.trace if s["type"] == "tool_call")
        invented = [w for w in vocab if _mentions(answer, w) and not _mentions(evidence, w)]
        checks.append(Check("grounding", "no invented facts", not invented,
                            f"not in any tool result: {invented}" if invented else ""))
    return checks


# Ablation ladder: each level adds one part of the architecture to the one before it.
LEVELS = {
    "baseline": "no tools; starting memory pasted into the prompt as text",
    "sensors":  "sensor tools only; starting memory as text (a plain tool-using agent, no memory layer)",
    "plain":    "all 8 tools incl. the memory layer; no safeguards",
    "checks":   "+ tool-layer checks: memory check, grounded writes, disagreement summary, safe moves",
    "full":     "+ answer self-check (the complete system)",
}
SENSOR_TOOLS = ["read_lidar", "read_camera", "get_pose", "move"]
SENSORS_PROMPT = Path(__file__).parent / "prompts" / "system_sensors.md"


def level_options(level: str) -> tuple[dict, bool]:
    """(ToolRegistry options, self_check) for a level."""
    on = level in ("checks", "full")
    tools = {"memory_check": on, "grounded_writes": on, "disagreement_summary": on, "safe_moves": on}
    if level == "sensors":
        tools["allowed_tools"] = SENSOR_TOOLS
    return tools, level == "full"


def run_scenario(scenario: dict, llm, level: str = "full", on_turn=None) -> dict:
    """Run every user turn of a scenario at the given level, then check the outcome."""
    if level not in LEVELS:
        raise ValueError(f"unknown level {level!r}; choose from {list(LEVELS)}")
    user_turns = scenario["turns"]
    store = None
    if level == "baseline":
        turns = [run_baseline(llm, scenario.get("memory", []), user_turns)]
    else:
        tool_options, self_check = level_options(level)
        world = build_world(scenario, **tool_options)
        prompt = None
        if level == "sensors":
            prompt = (SENSORS_PROMPT.read_text(encoding="utf-8") +
                      "\nYour stored knowledge:\n" + memory_as_text(scenario))
        agent = Agent(world.tools, llm, system_prompt=prompt, self_check=self_check)
        turns = []
        for q in user_turns:
            result = agent.ask(q)
            turns.append(result)
            if on_turn:
                on_turn(result)
        store = world.store
    # Levels that were shown their memory as text may repeat facts from it: those count as grounded.
    extra = json.dumps(scenario.get("memory", [])) if level in ("baseline", "sensors") else ""
    checks = run_checks(scenario.get("expect", {}), turns, store, user_turns, extra)
    return {
        "scenario": scenario["id"],
        "set": scenario.get("set"),
        "type": scenario.get("type"),
        "mode": level,
        "model": getattr(llm, "model", "?"),
        "turns": [asdict(t) for t in turns],
        "final_beliefs": store.to_dict() if store else None,
        "checks": [asdict(c) for c in checks],
        "passed": all(c.passed for c in checks),
    }
