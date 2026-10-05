"""Run the full experiment matrix in priority order, then build the results report.

    python run_experiments.py                   # local qwen2.5:7b via Ollama (about 5 hours)
    python run_experiments.py --quick           # 1 run per level at T=0 (about 2 hours)
    python run_experiments.py --skip-done       # skip combinations that already have results
    python run_experiments.py --dry-run         # print the commands only

Most important first, so partial results are still useful if it is stopped early:
held-out set first (it measures generalisation), then the dev-set ablation ladder, then
repeats at temperature 0.7 (at temperature 0 repeated runs are nearly identical).
The dev-set "full" level already has 5 runs from 28 Sep, so it is only repeated at 0.7.

Owner: Udit
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

MATRIX = [
    # (set, level, runs, temperature)
    ("heldout", "full", 3, 0.0),
    ("heldout", "plain", 3, 0.0),
    ("heldout", "baseline", 3, 0.0),
    ("heldout", "sensors", 3, 0.0),
    ("dev", "plain", 3, 0.0),
    ("dev", "sensors", 3, 0.0),
    ("dev", "checks", 3, 0.0),
    ("dev", "baseline", 3, 0.0),
    ("heldout", "full", 3, 0.7),
    ("dev", "full", 3, 0.7),
]

# At temperature 0 repeated runs are nearly identical, so one run per level is enough there;
# the repeats that measure spread are the temperature-0.7 ones.
QUICK = [
    ("heldout", "full", 3, 0.0),
    ("heldout", "plain", 1, 0.0),
    ("heldout", "baseline", 1, 0.0),
    ("heldout", "sensors", 1, 0.0),
    ("dev", "plain", 1, 0.0),
    ("dev", "sensors", 1, 0.0),
    ("dev", "checks", 1, 0.0),
    ("dev", "baseline", 1, 0.0),
    ("heldout", "full", 2, 0.7),
    ("heldout", "plain", 2, 0.7),
]


def already_done(set_name: str, level: str, temp: float, model: str) -> bool:
    tag = model.replace("/", "-").replace(":", "-") + (f"_t{temp:g}" if temp else "")
    return any((d / "summary.md").exists() for d in Path("logs").glob(f"*_{set_name}_{level}_{tag}"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--provider", default="ollama")
    ap.add_argument("--model", default="qwen2.5:7b")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--quick", action="store_true", help="1 run per level at T=0, 2 held-out repeats at T=0.7")
    ap.add_argument("--skip-done", action="store_true", help="skip combinations that already have a summary")
    args = ap.parse_args()

    matrix = QUICK if args.quick else MATRIX
    for i, (set_name, level, runs, temp) in enumerate(matrix, 1):
        if args.skip_done and already_done(set_name, level, temp, args.model):
            print(f"[{i}/{len(matrix)}] skip {set_name} {level} T={temp} (already done)", flush=True)
            continue
        cmd = [sys.executable, "-u", "evaluate.py", "--set", set_name, "--level", level, "--runs", str(runs),
               "--temperature", str(temp), "--provider", args.provider, "--model", args.model]
        print(f"[{i}/{len(matrix)}] {time.strftime('%H:%M')}  {set_name:<8} {level:<9} x{runs}  T={temp}", flush=True)
        if not args.dry_run:
            subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL)
    if not args.dry_run:
        subprocess.run([sys.executable, "report.py"], check=False)
    print(f"done {time.strftime('%H:%M')}", flush=True)


if __name__ == "__main__":
    main()
