# I, Agent

A three-layer epistemic architecture for grounded LLM agents (AI course project).

Team: **Siddh** (memory layer), **Rudraksh** (LLM layer), **Udit** (world layer and evaluation).

An LLM agent that checks its beliefs against a structured memory and live (simulated) sensors,
knows where every belief came from, and keeps the user's, its own, and other robots' viewpoints separate.

```
DECLARATIVE   declarative.py              (Siddh)     belief graph (NetworkX) + provenance log (SQLite)
      ▲
      │  query_beliefs · update_belief · record_user_belief · get_provenance
      ▼
PROCEDURAL    procedural.py, tools.py     (Rudraksh)  LLM in a ReAct loop with tool calling
      ▲
      │  read_lidar · read_camera · get_pose · move
      ▼
SENSORIMOTOR  sensorimotor.py             (Udit)      mock world: routes, objects, lighting
```

The LLM can reach the other two layers only through tools, so every fact in an answer can be
traced to a specific tool result in the log.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows; on macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # then put your Groq key in .env (free at console.groq.com)
```

## Run

```bash
python -m pytest                  # offline unit tests, no API key needed
python run_scenario.py --list     # the 10 scenarios
python run_scenario.py A1         # Scenario A live, with the full trace (the demo)
python run_scenario.py B1         # Scenario B: user thinks red, camera sees brown, log says blue
python run_scenario.py A1 --chat  # then ask your own questions
python evaluate.py                # all 10 scenarios x 5 runs -> logs/<time>_agent_<model>/
python evaluate.py --baseline     # same LLM with memory as plain text and no tools
```

### Models and limits

- **Groq (default):** `openai/gpt-oss-20b`, open-weight, fast. Groq no longer serves Llama 3.
  The free tier allows about **200k tokens per model per day**, and one scenario run uses 6–12k
  tokens. So one key covers roughly one full pass of the suite per day. Use Groq for the live demo.
- **Ollama (local, unlimited):** `qwen2.5:7b` (already pulled) or the spec's Llama:
  `ollama pull llama3.1:8b`. Add `--provider ollama --model qwen2.5:7b` to any command.
  Slower (about 1–2 minutes per scenario) but free and offline. Use it for the full test suite.
- To spread Groq usage, each teammate can use their own key and run a subset:
  `python evaluate.py --only A1 A2 A3`.

## Code map

| File | Owner | What it does |
|---|---|---|
| `i_agent/schemas.py` | team | Data contracts: `Belief`, `ProvenanceRecord`, `SensorReading`, `ToolResult` |
| `i_agent/declarative.py` | Siddh | Belief graph, provenance log, conflict rule, snapshots and diffs |
| `i_agent/tools.py` | Rudraksh | Tool schemas the LLM sees, and safe execution |
| `i_agent/procedural.py` | Rudraksh | ReAct loop, LLM client, retries, no-tools baseline |
| `i_agent/prompts/system.md` | Rudraksh | The epistemic rules given to the LLM |
| `i_agent/sensorimotor.py` | Udit | Mock environment: LiDAR, camera with lighting, motion |
| `i_agent/scenario.py` | Udit | Builds the three layers from a scenario file |
| `i_agent/evaluation.py` | Udit | Automatic checks: answer, tools, memory, grounding |
| `scenarios/*.json` | all | The 10 test scenarios (the project's data) |
| `run_scenario.py` | Udit | Demo script with the printed trace |
| `evaluate.py` | Udit | Test suite runner, logs and results table |

## Key design decisions

- **Perspectives.** Every belief carries a perspective: `self`, `map`, `user` or `agent:<id>`.
  They sit side by side in the graph (edge key `predicate|perspective`), so "what the user thinks",
  "what I see" and "what the records say" never overwrite one another.
- **Conflict rule** (in `declarative.py`). When the agent writes its own belief from a live sensor
  and it contradicts the static map, the map belief's confidence is multiplied by 0.3 and the
  change is logged. User and other-robot beliefs are never downgraded automatically.
- **Provenance.** Every write goes to SQLite with old value, new value, source, confidence, time and reason.
- **Epistemic state as a sequence of graphs.** The graph is snapshotted before and after each turn;
  `diff()` shows exactly what the agent changed.
- **Simulated clock.** All times come from `SimClock`, so runs are reproducible.

## Evaluation

Each scenario file has an `expect` block. `evaluation.py` checks four things per run:

| Check | Question it answers |
|---|---|
| answer | Does the final answer say the right things? |
| tools | Did the agent consult the layers it needed, instead of answering from nowhere? |
| memory | Is the belief graph in the correct state afterwards? |
| grounding | Is every colour/value in the answer present in some tool result or user message? |

The baseline gets the same memory as plain text but no tools. It cannot read sensors or update
beliefs, which shows what the architecture adds.

## Scenarios

| Id | Tests |
|---|---|
| A1_route_blocked | Spec Scenario A: map clear, LiDAR blocked at 12 cm |
| A2_route_reopened | Map blocked, LiDAR clear |
| A3_noisy_lidar | One spurious reading; agent must re-read before updating |
| A4_object_missing | Map says the box is here; camera does not see it |
| A5_stale_belief | Own belief is two hours old; must re-check |
| B1_three_colors | Spec Scenario B: user red / camera brown / log blue |
| B2_false_belief | User's false belief about where the box is (Sally-Anne) |
| B3_conflicting_reports | Two robots disagree about the colour |
| H1_unknown_object | Asked about something unknown; must say it does not know |
| P1_provenance | Must cite where and when a belief came from |

## Explaining your part (for the evaluation)

**Siddh (memory, `declarative.py`).** Beliefs are edges in a NetworkX MultiDiGraph keyed by
`predicate|perspective`, so the map's, the user's and other robots' views of the same fact coexist.
Every write goes through `_write()`, which also inserts a provenance row into SQLite. `assert_belief()`
applies the conflict rule: a sensor-based `self` belief that contradicts a `map` belief multiplies
the map's confidence by 0.3. User and other-robot beliefs are never downgraded, because they are other minds' views.
`snapshot()` and `diff()` store the epistemic state as a sequence of graphs.

**Rudraksh (LLM, `procedural.py`, `tools.py`, `prompts/system.md`).** A hand-written ReAct loop over the
OpenAI-compatible API (Groq or Ollama). Tools are the only path to the other layers. Safeguards, each added
after a failure we actually observed in the logs:
1. **Memory check on every sensor reading.** Sensor results carry a `memory_check` listing the stored
   beliefs the reading contradicts, so the conflict cannot be overlooked.
2. **Grounded writes.** `update_belief` refuses any value that never appeared in a tool result. We saw a
   model invent "the map says red" and write it into memory; now that is impossible.
3. **Answer self-check** (`check_answer`), which sends a draft answer back to the LLM (up to 4 times) if:
   - it never consulted memory,
   - it claims "I updated my belief" without calling `update_belief`,
   - it announces an action ("I will check…") without doing it,
   - a sensor-vs-memory conflict is still unresolved,
   - it relies on the static map for something a sensor could check right now,
   - it gives properties to an entity no tool returned (e.g. calling `crate_07` blue because `box_01` is),
   - the user stated a belief ("I left the box in…") that was never recorded.
4. **Small-model tolerance.** Plain parameter names (`entity`, `property`, `value`), alias mapping,
   tool calls written as text are parsed and executed, and malformed calls are retried with the API's
   error message.

`python evaluate.py --no-self-check` switches item 3 off, which measures how much it contributes.

**Udit (world and evaluation, `sensorimotor.py`, `scenario.py`, `evaluation.py`).** `MockEnv` holds the
ground truth (obstacles, objects, lighting) and exposes it only through sensors. Yellow light shifts
perceived colours, and a LiDAR script can inject noise. Scenario JSON files are the data. `evaluation.py`
scores each run on four axes (answer, tools, memory, grounding). `evaluate.py` repeats each scenario,
writes JSON logs, and runs the no-tools baseline and the no-self-check ablation.

## Results so far (26 Sep 2026, `qwen2.5:7b` via Ollama, 1 run per scenario)

| | Agent (three layers) | Baseline (same model, memory as text, no tools) |
|---|---|---|
| Runs passing every check | **9/10** | 0/10 (cannot pass tool or memory checks by design) |
| Correct final answer | **9/10** | 5/10 |
| Scenario A (map says clear, LiDAR says blocked) | Detects the obstacle, updates memory, downgrades the map | "Yes, my route is clear." |

The only agent failure is B3. It trusts the newer record correctly, but leaves out the older conflicting one.
Logs: `logs/20260926-154149_agent_qwen2.5-7b/` and `logs/20260926-150521_baseline_qwen2.5-7b/`.

Still to do: 5 runs per scenario, the `--no-self-check` ablation, and the same suite on Groq's `openai/gpt-oss-20b`.

## Notes on the evaluation

- **The baseline scores 0 by design on the tools and memory checks**, since it has no tools. Compare it
  with the agent on the *answer* column only. That is where the baseline gives the wrong answer on
  Scenario A: it trusts the map and says the route is clear.
- **Changes made after seeing results (both to H1 only):**
  1. It first required `query_beliefs` specifically. It now accepts either memory tool
     (`query_beliefs` or `get_provenance`), because the test's intent is "consulted memory before answering".
  2. Its list of "I don't know" phrases missed a correct answer ("I have no memory record ... cannot
     provide any information"), so a few phrasings were added. The saved logs were re-checked with
     `python evaluate.py --rescore <folder>`.

  Every other expectation is unchanged from when it was written.
- **Weak keyword checks.** A4's answer check accepts words as broad as "no" and "not". The baseline's
  "correct" A4 answer therefore passes on wording alone. Tightening it is a good next step.
- **Sample size.** Results so far are 1 run per scenario on `qwen2.5:7b`. LLM output varies between runs,
  so report pass rates over 5 runs (`python evaluate.py --provider ollama --model qwen2.5:7b`) before
  drawing conclusions.
- **Development history.** `logs/dev_iterations/` keeps the earlier runs, from before each safeguard was
  added. They show which failures each safeguard fixed, which is useful for the report.
