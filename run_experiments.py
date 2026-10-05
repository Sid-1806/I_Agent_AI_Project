"""Run the full experiment matrix in priority order, then build the results report.

    python run_experiments.py                   # local qwen2.5:7b via Ollama (about 5-6 hours)
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


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--provider", default="ollama")
    ap.add_argument("--model", default="qwen2.5:7b")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for i, (set_name, level, runs, temp) in enumerate(MATRIX, 1):
        cmd = [sys.executable, "-u", "evaluate.py", "--set", set_name, "--level", level, "--runs", str(runs),
               "--temperature", str(temp), "--provider", args.provider, "--model", args.model]
        print(f"[{i}/{len(MATRIX)}] {time.strftime('%H:%M')}  {set_name:<8} {level:<9} x{runs}  T={temp}", flush=True)
        if not args.dry_run:
            subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL)
    if not args.dry_run:
        subprocess.run([sys.executable, "report.py"], check=False)
    print(f"done {time.strftime('%H:%M')}", flush=True)


if __name__ == "__main__":
    main()
