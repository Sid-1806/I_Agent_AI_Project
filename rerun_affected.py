"""Bring saved full-system runs up to the current system version without rerunning all of them.

    python rerun_affected.py logs/<run folder> [more folders] [--dry-run]

For v4 -> v4.1 the code changed in two places, both inside the answer self-check (see
i_agent/__init__.py). This script replays every saved run's trace through those two places:

  1. would the system have recorded a user-stated belief itself (no successful
     record_user_belief before a draft, and the user's words fully determine the call)?
  2. would the self-check have rejected a draft that claims what is in a room no tool result
     mentions ("no objects in Room 309"), or that reports a colour seen under yellow or dim light
     without the lighting and the other recorded colours, or that answers while records disagree
     about a route the robot faces and nobody has scanned it?

If neither happens at any draft, the model would have received exactly the same messages, so at
temperature 0 the v4.1 run is the saved run: it is carried over, marked "carried_over" with the
source file. Otherwise the scenario is run again with the current code. The result is one new
log folder per input folder, labelled with the current SYSTEM_VERSION, holding both kinds.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

from i_agent import SYSTEM_VERSION
from i_agent.procedural import (_EMPTY_ROOM_CLAIM, _SAYS_UNKNOWN, _disputed_unscanned_routes,
                                _distorted_colour_problems, _USER_STATES, _observed_entities,
                                _user_belief_call)


def why_affected(rec: dict, facing: dict) -> str:
    """Why the current code could behave differently on this saved run ('' if it could not).
    `facing` is the scenario's starting direction -> route map."""
    if rec.get("mode") != "full" or "error" in rec:
        return "not a completed full-system run" if rec.get("mode") == "full" else ""
    history: list[dict] = []
    user_turns: list[str] = []
    for turn in rec["turns"]:
        user_turns.append(turn["question"])
        trace = turn["trace"]
        for i, step in enumerate(trace):
            if step["type"] not in ("draft", "answer"):
                continue
            prior = history + trace[:i]
            text = step["text"]
            stated = [q for q in user_turns if _USER_STATES.search(q)]
            recorded = any(s["type"] == "tool_call" and s["name"] == "record_user_belief" and s["result"].get("ok")
                           for s in prior)
            if stated and not recorded and "<" not in _user_belief_call(stated[0]):
                return "the system would record the user's stated belief"
            observed = _observed_entities(prior)
            if _disputed_unscanned_routes(prior, facing):
                return "the self-check would ask for a LiDAR reading of a disputed route"
            if _distorted_colour_problems(text, prior):
                return "the self-check would ask about a colour seen under distorting light"
            claims = {n for m in _EMPTY_ROOM_CLAIM.finditer(text) for n in m.groups() if n}
            if any(f"room_{n}" not in observed for n in claims) and not _SAYS_UNKNOWN.search(text):
                return f"the self-check would reject a claim about Room {', '.join(sorted(claims))}"
        history += trace
    return ""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folders", nargs="+", type=Path)
    ap.add_argument("--dry-run", action="store_true", help="only list which runs would be rerun")
    ap.add_argument("--provider", default="ollama")
    ap.add_argument("--model", default="qwen2.5:7b-8k")
    args = ap.parse_args()

    from evaluate import summarise
    from i_agent.scenario import all_scenarios
    for folder in args.folders:
        recs = {f: json.loads(f.read_text(encoding="utf-8")) for f in sorted(folder.glob("*_run*.json"))}
        set_name = next(iter(recs.values()))["set"]
        rerun = {}
        facing = {sc["id"]: sc["world"]["robot"].get("facing") or {} for sc in all_scenarios(set_name)}
        for f, rec in recs.items():
            reason = why_affected(rec, facing.get(rec["scenario"], {}))
            if reason:
                rerun[rec["scenario"]] = reason
        done = {rec["scenario"] for rec in recs.values()}
        for sc in all_scenarios(set_name):
            if sc["id"] not in done:
                rerun[sc["id"]] = "no saved run (the original pass did not finish)"
        print(f"{folder.name}: {len(recs)} runs, {len(rerun)} to run")
        for sid, reason in rerun.items():
            print(f"  rerun {sid:<28} {reason}")
        if args.dry_run:
            continue
        before = set(Path("logs").iterdir())
        if rerun:
            subprocess.run([sys.executable, "-u", "evaluate.py", "--set", set_name, "--level", "full", "--runs", "1",
                            "--provider", args.provider, "--model", args.model, "--only", *rerun],
                           check=True, stdout=subprocess.DEVNULL)
            # the new folder of this set that holds the reruns (another evaluation may be running too)
            out = max(d for d in set(Path("logs").iterdir()) - before
                      if f"_{set_name}_full_" in d.name and any(d.glob(f"{next(iter(rerun))}_run*.json")))
        else:
            out = Path("logs") / f"{time.strftime('%Y%m%d-%H%M%S')}_{set_name}_full_{folder.name.split('_full_')[-1]}"
            out.mkdir()
        for f, rec in recs.items():
            if rec["scenario"] in rerun:
                continue
            rec["system"] = SYSTEM_VERSION
            rec["carried_over"] = {"from": str(f).replace("\\", "/"),
                                   "why": "no v4.1 change would have fired at any draft; identical prompts at T=0"}
            (out / f.name).write_text(json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")
        records = defaultdict(list)
        for f in sorted(out.glob("*_run*.json")):
            rec = json.loads(f.read_text(encoding="utf-8"))
            records[rec["scenario"]].append(rec)
        title = (f"Results: {set_name} set, level full, {args.model}, temperature 0, 1 runs per scenario "
                 f"({SYSTEM_VERSION}: {len(rerun)} run again, {sum(r not in rerun for r in done)} carried over from {folder.name})")
        summarise(records, all_scenarios(set_name), title, out)
        print(f"  -> {out}")


if __name__ == "__main__":
    main()
