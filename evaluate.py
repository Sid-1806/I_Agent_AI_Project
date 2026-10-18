"""Run the epistemic test suite and write logs plus a results table.

    python evaluate.py                         # dev set, full system, 5 runs each
    python evaluate.py --set heldout           # the frozen held-out set
    python evaluate.py --level plain           # ablation level (see below)
    python evaluate.py --runs 1 --only A1 B1   # quick check
    python evaluate.py --model openai/gpt-oss-120b
    python evaluate.py --rescore logs/<run>    # re-check saved logs against the current scenario
                                               # expectations, without calling the LLM
    python evaluate.py --report                # one table and chart of every run in logs/

Levels (each adds one part of the architecture):
    baseline  no tools; starting memory pasted into the prompt as text
    sensors   sensor tools only; memory as text (plain tool-using agent, no memory layer)
    plain     all 8 tools incl. the memory layer; no safeguards
    checks    + tool-layer checks (memory check, grounded writes, disagreement summary)
    full      + answer self-check (the complete system)
--baseline and --no-self-check are kept as shortcuts for --level baseline / --level checks.

Output goes to logs/<time>_<set>_<level>_<model>/: one JSON log per run, plus summary.md and summary.csv.

Owner: Udit
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path

from i_agent import SYSTEM_VERSION
from i_agent.clock import SimClock
from i_agent.declarative import BeliefStore
from i_agent.evaluation import LEVELS, run_checks, run_scenario
from i_agent.procedural import AgentResult
from i_agent.schemas import Belief
from i_agent.scenario import SETS, all_scenarios

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

KINDS = ["answer", "tools", "memory", "grounding"]


def summarise(records: dict[str, list[dict]], scenarios: list[dict], title: str, out: Path) -> None:
    rows = []
    for s in scenarios:
        recs = records.get(s["id"], [])
        if not recs:
            continue
        kind_pass: dict[str, list[bool]] = defaultdict(list)
        failures: Counter = Counter()
        for rec in recs:
            by_kind = defaultdict(list)
            for c in rec["checks"]:
                by_kind[c["kind"]].append(c["passed"])
                if not c["passed"]:
                    failures[c["name"]] += 1
            for k, v in by_kind.items():
                kind_pass[k].append(all(v))
            if "error" in rec:
                failures[rec["error"][:80]] += 1
        row = {"scenario": s["id"], "type": s.get("type"),
               "pass_rate": f"{sum(r['passed'] for r in recs)}/{len(recs)}"}
        for k in KINDS:
            row[k] = f"{sum(kind_pass[k])}/{len(kind_pass[k])}" if kind_pass[k] else "-"
        row["most_common_failure"] = failures.most_common(1)[0][0] if failures else ""
        rows.append(row)

    passed = sum(int(r["pass_rate"].split("/")[0]) for r in rows)
    total = sum(int(r["pass_rate"].split("/")[1]) for r in rows)
    header = ["scenario", "type", "pass_rate", *KINDS, "most_common_failure"]
    with open(out / "summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)
    md = [f"# {title}", "", f"Overall: {passed}/{total} runs passed all checks", "",
          "| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    md += ["| " + " | ".join(str(r[h]) for h in header) + " |" for r in rows]
    (out / "summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n" + "\n".join(md))


def rescore(log_dir: Path, scenarios: list[dict]) -> None:
    """Recompute every check of saved runs with the scenarios' current expectations."""
    by_id = {s["id"]: s for s in scenarios}
    records: dict[str, list[dict]] = defaultdict(list)
    for f in sorted(log_dir.glob("*_run*.json")):
        rec = json.loads(f.read_text(encoding="utf-8"))
        s = by_id.get(rec["scenario"])
        if s is None or "error" in rec:
            records[rec["scenario"]].append(rec)
            continue
        turns = [AgentResult(**t) for t in rec["turns"]]
        store = None
        if rec.get("final_beliefs") is not None:
            store = BeliefStore(SimClock())
            store.load([Belief(**b) for b in rec["final_beliefs"]], reason="rescore")
        extra = json.dumps(s.get("memory", [])) if rec.get("mode") in ("baseline", "sensors") else ""
        checks = run_checks(s.get("expect", {}), turns, store, s["turns"], extra)
        rec["checks"] = [asdict(c) for c in checks]
        rec["passed"] = all(c.passed for c in checks)
        rec["rescored"] = time.strftime("%Y-%m-%d %H:%M")
        f.write_text(json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")
        records[rec["scenario"]].append(rec)
    old = (log_dir / "summary.md").read_text(encoding="utf-8").splitlines()[0] if (log_dir / "summary.md").exists() else ""
    title = re.sub(r"^# ", "", old) or log_dir.name
    summarise(records, scenarios, f"{title} (rescored {time.strftime('%Y-%m-%d %H:%M')})", log_dir)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--only", nargs="*", help="scenario id prefixes to run, e.g. A1 B1")
    ap.add_argument("--set", default="dev", choices=SETS, help="scenario set (default dev)")
    ap.add_argument("--level", default="full", choices=list(LEVELS), help="ablation level (default full)")
    ap.add_argument("--baseline", action="store_true", help="shortcut for --level baseline")
    ap.add_argument("--no-self-check", action="store_true", help="shortcut for --level checks")
    ap.add_argument("--report", action="store_true", help="summarise every run folder in logs/")
    ap.add_argument("--rescore", type=Path, help="re-check the saved logs in this folder; no LLM calls")
    ap.add_argument("--provider")
    ap.add_argument("--model")
    ap.add_argument("--delay", type=float, default=0.0, help="seconds to wait between runs (rate limits)")
    ap.add_argument("--temperature", type=float, default=0.0,
                    help="sampling temperature (default 0; at 0 repeated runs are nearly identical)")
    args = ap.parse_args()

    if args.report:
        from report import main as report_main
        report_main()
        return
    if args.rescore:
        rescore(args.rescore, [s for name in SETS for s in all_scenarios(name)])
        return
    scenarios = [s for s in all_scenarios(args.set)
                 if not args.only or any(s["id"].startswith(p) for p in args.only)]

    from i_agent.procedural import OpenAICompatibleLLM
    llm = OpenAICompatibleLLM(provider=args.provider, model=args.model, temperature=args.temperature)
    mode = "baseline" if args.baseline else ("checks" if args.no_self_check else args.level)
    model_tag = llm.model.replace('/', '-').replace(':', '-') + (f"_t{args.temperature:g}" if args.temperature else "")
    out = Path("logs") / f"{time.strftime('%Y%m%d-%H%M%S')}_{args.set}_{mode}_{model_tag}"
    out.mkdir(parents=True, exist_ok=True)
    print(f"{len(scenarios)} {args.set} scenarios × {args.runs} runs, level {mode}, model {llm.model} → {out}\n")

    records: dict[str, list[dict]] = defaultdict(list)
    for s in scenarios:
        for i in range(1, args.runs + 1):
            try:
                rec = run_scenario(s, llm, level=mode)
            except Exception as e:  # noqa: BLE001 - record API failures and keep going
                rec = {"scenario": s["id"], "set": args.set, "mode": mode,
                       "error": f"{type(e).__name__}: {e}", "checks": [], "passed": False}
            rec["system"] = SYSTEM_VERSION
            (out / f"{s['id']}_run{i}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False),
                                                         encoding="utf-8")
            records[s["id"]].append(rec)
            print(f"  {s['id']:<24} run {i}: {'PASS' if rec['passed'] else 'FAIL'}")
            if args.delay:
                time.sleep(args.delay)

    summarise(records, scenarios, f"Results: {args.set} set, level {mode}, {llm.model}, temperature {args.temperature:g}, {args.runs} runs per scenario", out)


if __name__ == "__main__":
    main()
