"""Replay viewer: shows the three layers working, step by step, for real evaluation runs.

    python ui.py                       # latest v2 full-system run of every scenario
    python ui.py logs/<folder>         # every run in one log folder
    python ui.py logs/<folder>/A1_route_blocked_run1.json ...

Writes ui/viewer.html (one file, works offline). Open it in a browser.

The viewer does not call the LLM. For each logged run it rebuilds the scenario's world and memory,
then re-executes the run's tool calls in order through the same ToolRegistry. The layers are
deterministic, so this reproduces the state of the world, the brain's trace and the belief graph
after every step. Each replayed tool result is compared with the logged one; a mismatch is shown.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from i_agent.evaluation import level_options
from i_agent.scenario import build_world, load_scenario

OUT = Path("ui") / "viewer.html"
TEMPLATE = Path("ui") / "template.html"
V2_SINCE = "20261018-200000"


def default_runs() -> list[Path]:
    """Run 1 of each scenario from the newest v2 full-system folder (temperature 0) of each set."""
    newest: dict[str, Path] = {}
    for folder in sorted(Path("logs").glob("2*_full_*")):
        if folder.name < V2_SINCE or "_t0." in folder.name:
            continue
        set_name = folder.name.split("_")[1]
        newest[set_name] = folder
    files = []
    for set_name in ("dev", "heldout2", "heldout"):
        if set_name in newest:
            files += sorted(newest[set_name].glob("*_run1.json"))
    return files


def beliefs(store) -> list[dict]:
    now = store.clock.now()
    return [{"s": b.subject, "p": b.predicate, "o": b.obj, "persp": b.perspective, "src": b.source,
             "conf": b.confidence, "age": round(now - b.timestamp)} for b in store.query()]


def provenance(store) -> list[dict]:
    rows = store.db.execute("SELECT * FROM provenance ORDER BY id").fetchall()
    return [{"s": r["subject"], "p": r["predicate"], "persp": r["perspective"], "old": r["old_obj"],
             "new": r["new_obj"], "oc": r["old_confidence"], "nc": r["new_confidence"], "src": r["source"],
             "reason": r["reason"]} for r in rows]


def replay(log_path: Path) -> dict:
    log = json.loads(log_path.read_text(encoding="utf-8"))
    scenario = load_scenario(log["scenario"])
    level = log.get("mode", "full")
    tool_options, _ = level_options(level if level in ("plain", "checks", "full", "sensors") else "full")
    world = build_world(scenario, **tool_options)
    tools, store, env = world.tools, world.store, world.env

    def frame(turn: int, step: dict, **extra) -> dict:
        return {"turn": turn, "type": step["type"], "name": step.get("name"), "args": step.get("arguments"),
                "text": step.get("text"), "room": env.robot["room"], "clock": store.clock.now(),
                "beliefs": beliefs(store), "prov": len(provenance(store)), **extra}

    frames = [{"turn": 0, "type": "start", "room": env.robot["room"], "clock": store.clock.now(),
               "beliefs": beliefs(store), "prov": len(provenance(store))}]
    mismatches = 0
    for t, turn in enumerate(log["turns"], 1):
        tools.open_conflicts.clear()
        tools.scanned.clear()
        frames.append({"turn": t, "type": "question", "text": turn["question"], "room": env.robot["room"],
                       "clock": store.clock.now(), "beliefs": beliefs(store), "prov": len(provenance(store))})
        for step in turn["trace"]:
            if step["type"] != "tool_call":
                frames.append(frame(t, step))
                continue
            result = json.loads(tools.execute(step["name"], step.get("arguments") or {}))
            same = result == step["result"]
            mismatches += not same
            frames.append(frame(t, step, result=result, mismatch=not same))
    return {"id": log["scenario"], "set": log.get("set", "dev"), "level": level,
            "system": log.get("system", "v1"), "model": log.get("model"), "passed": log.get("passed"),
            "file": str(log_path).replace("\\", "/"), "description": scenario.get("description", ""),
            "world": scenario.get("world", {}), "frames": frames, "provenance": provenance(store),
            "checks": log.get("checks", []), "mismatches": mismatches}


def main() -> None:
    args = [Path(a) for a in sys.argv[1:]]
    files = []
    for a in args:
        files += sorted(a.glob("*_run*.json")) if a.is_dir() else [a]
    files = files or default_runs()
    if not files:
        sys.exit("no logs found; run evaluate.py first")
    runs = []
    for f in files:
        try:
            runs.append(replay(f))
        except Exception as e:  # noqa: BLE001 - skip logs that cannot be replayed (e.g. baseline runs)
            print(f"skip {f}: {e}")
    data = json.dumps(runs, ensure_ascii=False).replace("</", "<\\/")
    OUT.write_text(TEMPLATE.read_text(encoding="utf-8").replace("/*DATA*/[]", data), encoding="utf-8")
    bad = [r["id"] for r in runs if r["mismatches"]]
    print(f"wrote {OUT} with {len(runs)} runs" + (f"; replay differs from the log in: {bad}" if bad else ""))


if __name__ == "__main__":
    main()
