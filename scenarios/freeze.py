"""Freeze a scenario set: record each file's SHA-256 in <set>/FROZEN.md before any run on it.

    python scenarios/freeze.py heldout3 [--author "who wrote them, and how"]
"""
import argparse
import datetime
import hashlib
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("set_name")
ap.add_argument("--author", default="")
args = ap.parse_args()

folder = Path(__file__).parent / args.set_name
files = sorted(folder.glob("*.json"))
if not files:
    raise SystemExit(f"no scenario files in {folder}")
hashes = "\n".join(f"- `{hashlib.sha256(f.read_bytes()).hexdigest()}`  `{f.name}`" for f in files)
when = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
text = f"""# {args.set_name}: frozen

Frozen on {when} (local time), before the agent was run on any of them.
{('Written by: ' + args.author) if args.author else ''}

## Rules

1. These files must not change. `tests/test_scenarios.py` fails if any hash below stops matching.
2. No code or prompt changes are made because of results on this set; if the system changes later,
   results on this set are reported separately for each version.

## SHA-256 of each file

{hashes}
"""
(folder / "FROZEN.md").write_bytes(text.encode("utf-8"))
print(f"froze {len(files)} files in {folder / 'FROZEN.md'}")
