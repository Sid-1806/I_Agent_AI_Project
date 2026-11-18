# Handoff: where the project stands (18 Nov 2026)

Read `README.md` for setup, the architecture and the evaluation method. This note says what is
done and what to do next.

## Get it running

```bash
pip install -r requirements.txt
ollama pull qwen2.5:7b
ollama create qwen2.5:7b-8k -f ollama/Modelfile     # 8k context; the 4k default drops the system prompt
python -m pytest                                    # 103 tests, no LLM needed
python server.py                                    # web UI on http://localhost:8000
```

`.env` (Groq key) is not included. Copy `.env.example` to `.env` and add your own key if you
want to use Groq instead of local Ollama.

## Current state

- **System version v4** (`SYSTEM_VERSION` in `i_agent/__init__.py`): weighted confidence. Each
  live sensor reading updates the static map's confidence by Bayes' rule weighted by the sensor's
  reliability (replacing the old fixed x0.3), and records are compared by confidence discounted
  by age. See "Key design decisions" in the README.
- **Web UI** (`server.py` + `web/`): talk to the agent or replay a test log; the world is drawn
  as a floor plan with the robot, LiDAR beam and camera view; memory shows confidence changes.
  `web/dist` is already built, so Node is only needed to change the frontend.
- **Last complete results** are for **v3**: every completed run passed (dev 13/13 with 2 API
  timeouts, held-out set 1 10/10, held-out set 2 11/11). Clean v2 held-out set 2: 27/33.
- **v4 has not had a complete run yet.** The last attempt passed A1-A5 and B1, then was
  stopped for this handoff. Earlier v4 attempts each exposed a problem that was fixed (see
  `git log`); their logs are in `logs/dev_iterations/`.

## Next steps

1. Run all 36 scenarios on v4 (about 1-1.5 hours on a laptop GPU; keep the machine awake):
   ```bash
   python evaluate.py --set dev --runs 1 --provider ollama --model qwen2.5:7b-8k
   python evaluate.py --set heldout --runs 1 --provider ollama --model qwen2.5:7b-8k
   python evaluate.py --set heldout2 --runs 1 --provider ollama --model qwen2.5:7b-8k
   python report.py
   ```
   Look at any failure in the UI's Replay screen (or `logs/<run>/<scenario>_run1.json`).
   If you change code to fix one, say so in the commit and re-run all three sets, so the final
   numbers come from one code version.
2. Then repeat the full system 3 times per set for the report (`--runs 3`), and the ablation
   levels (`--level plain`, `checks`, `sensors`, `baseline`) if time allows:
   `python run_experiments.py --plan v2` runs the whole matrix.
3. Write the architecture verification report (a "desirable" deliverable in the proposal).

## Rules worth keeping

- Held-out sets (`scenarios/heldout`, `scenarios/heldout2`) are frozen: never edit those files
  (a test checks their SHA-256 hashes). Fixes driven by their failures must be reported as such.
- Results of different system versions are never pooled; bump `SYSTEM_VERSION` when behaviour changes.
