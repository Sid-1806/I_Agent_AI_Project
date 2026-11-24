"""Run the full experiment matrix in priority order, then build the results report.

    python run_experiments.py --plan v4         # the v4 system (weighted confidence): about 5-6 hours
    python run_experiments.py --plan v2         # the v2 system (18 Oct): about 5-6 hours
    python run_experiments.py                   # the v1 plan (mid-semester), about 5 hours
    python run_experiments.py --quick           # v1, 1 run per level at T=0 (about 2 hours)
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

# v2 system (see SYSTEM_VERSION in i_agent/__init__.py). Held-out set 2 first: it was frozen before
# any run, so it is the cleanest measure of generalisation. Then the 15-scenario dev set, then
# held-out set 1 (already seen under v1, so reported separately), then spread at temperature 0.7.
V2 = [
    ("heldout2", "full", 3, 0.0),
    ("heldout2", "baseline", 1, 0.0),
    ("heldout2", "sensors", 1, 0.0),
    ("heldout2", "plain", 1, 0.0),
    ("heldout2", "checks", 1, 0.0),
    ("dev", "full", 3, 0.0),
    ("dev", "baseline", 1, 0.0),
    ("dev", "sensors", 1, 0.0),
    ("dev", "plain", 1, 0.0),
    ("dev", "checks", 1, 0.0),
    ("heldout", "full", 3, 0.0),
    ("heldout2", "full", 2, 0.7),
]

# v4 system (weighted confidence). First one full pass over all 36 scenarios, then two more full
# passes (3 runs each in total), then one run of each lower level per set. Held-out set 2 was used
# to build v3, so v4 results on it are reported as seen, not as a clean test.
V4 = [
    ("dev", "full", 1, 0.0),
    ("heldout", "full", 1, 0.0),
    ("heldout2", "full", 1, 0.0),
    ("dev", "full", 2, 0.0),
    ("heldout", "full", 2, 0.0),
    ("heldout2", "full", 2, 0.0),
] + [(s, lv, 1, 0.0) for s in ("dev", "heldout", "heldout2") for lv in ("baseline", "sensors", "plain", "checks")]

# Shorter v4 plan (about 1.5 hours): one full-system pass over all four sets, including held-out
# set 3 (written without reading the code), plus the no-tools baseline on each set.
V4FAST = [(s, "full", 1, 0.0) for s in ("dev", "heldout", "heldout2", "heldout3")] +          [(s, "baseline", 1, 0.0) for s in ("dev", "heldout", "heldout2", "heldout3")]

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


def already_done(set_name: str, level: str, temp: float, model: str, since: str = "") -> bool:
    tag = model.replace("/", "-").replace(":", "-") + (f"_t{temp:g}" if temp else "")
    return any((d / "summary.md").exists() and d.name >= since
               for d in Path("logs").glob(f"*_{set_name}_{level}_{tag}"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--provider", default="ollama")
    ap.add_argument("--model", default="qwen2.5:7b-8k")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--plan", choices=["v1", "v2", "v4", "v4fast"], default="v4", help="which experiment plan to run")
    ap.add_argument("--quick", action="store_true", help="v1 plan: 1 run per level at T=0, 2 held-out repeats at T=0.7")
    ap.add_argument("--skip-done", action="store_true", help="skip combinations that already have a summary")
    args = ap.parse_args()

    matrix = {"v2": V2, "v4": V4, "v4fast": V4FAST}.get(args.plan) or (QUICK if args.quick else MATRIX)
    since = {"v2": "20261018-200000", "v4": "20261124-000000", "v4fast": "20261124-000000"}.get(args.plan, "")
    keep_awake(not args.dry_run)
    for i, (set_name, level, runs, temp) in enumerate(matrix, 1):
        if args.skip_done and already_done(set_name, level, temp, args.model, since):
            print(f"[{i}/{len(matrix)}] skip {set_name} {level} T={temp} (already done)", flush=True)
            continue
        cmd = [sys.executable, "-u", "evaluate.py", "--set", set_name, "--level", level, "--runs", str(runs),
               "--temperature", str(temp), "--provider", args.provider, "--model", args.model]
        print(f"[{i}/{len(matrix)}] {time.strftime('%H:%M')}  {set_name:<8} {level:<9} x{runs}  T={temp}", flush=True)
        if not args.dry_run:
            subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL)
    if not args.dry_run:
        subprocess.run([sys.executable, "report.py"], check=False)
    keep_awake(False)
    print(f"done {time.strftime('%H:%M')}", flush=True)


def keep_awake(on: bool) -> None:
    """On Windows, stop the computer idle-sleeping while the runs go (a closed lid still sleeps)."""
    if sys.platform == "win32":
        import ctypes
        ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | (ES_SYSTEM_REQUIRED if on else 0))


if __name__ == "__main__":
    main()
