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
python -m pytest                          # 81 offline tests, no API key needed
python run_scenario.py --list             # dev and held-out scenarios
python run_scenario.py A1                 # Scenario A live, with the full trace (the demo)
python run_scenario.py B1                 # Scenario B: user thinks red, camera sees brown, log says blue
python run_scenario.py A1 --level plain   # the same scenario with the safeguards switched off
python run_scenario.py A1 --chat          # then ask your own questions
python evaluate.py                        # dev set, full system, 5 runs -> logs/<time>_dev_full_<model>/
python evaluate.py --set heldout2         # held-out set 2 (frozen 18 Oct); --set heldout for set 1
python evaluate.py --level plain          # an ablation level (see "Evaluation")
python run_experiments.py --plan v2       # the whole matrix of sets x levels (5-6 hours locally)
python report.py                          # results/results.html, results.md, review.html
python server.py                          # the web UI on http://localhost:8000 (see "Web UI")
```

## Web UI

`python server.py` serves a React app (built into `web/dist`) on http://localhost:8000, with two
screens:

- **Talk to the agent.** Pick a world (any scenario), type a question or click one of the
  scenario's own questions, and watch all three layers as the agent works:
  - *World* (sensorimotor): the mock environment's ground truth as a map (rooms, roads, obstacles,
    lighting, objects in their true colour, the robot and its planned route), with a robot card
    showing the last LiDAR reading, what the camera saw, and any memory-check warning.
  - *Agent* (procedural): every LLM step as it streams in, including drafts rejected by the self-check.
  - *Memory* (declarative): the belief graph and the SQLite provenance log, with changed rows marked.
  The safeguards switch (all / tool checks only / none) shows live what they add. The timeline at
  the bottom steps through the run (arrow keys, space to play).
- **Replay a test log.** Any logged evaluation run, rebuilt step by step without calling the LLM,
  with its automatic checks.

A backend is needed because the agent is Python (NetworkX, SQLite, the mock world and the LLM loop);
`server.py` only wraps the existing classes and streams each step to the page. To change the frontend: `cd web && npm install && npm run dev` (port 5173,
with `server.py` running), then `npm run build`.

## Models and limits

- **Groq (default):** `openai/gpt-oss-20b`, open-weight, fast. Groq no longer serves Llama 3.
  The free tier allows about **200k tokens per model per day**, and one scenario run uses 6–12k
  tokens. So one key covers roughly one full pass of the suite per day. Use Groq for the live demo.
- **Ollama (local, unlimited):** `qwen2.5:7b`, or the spec's Llama: `ollama pull llama3.1:8b`.
  **Create the 8k-context variant once:** `ollama create qwen2.5:7b-8k -f ollama/Modelfile`, and use
  `--provider ollama --model qwen2.5:7b-8k`. Ollama's default context is 4096 tokens and it silently
  drops the start of longer conversations, including the system prompt; about one run in ten of the
  multi-turn scenarios was longer than that (all results before 19 Oct used the 4096 default).
  Slower (about 1–2 minutes per scenario) but free and offline. Use it for the full test suite.
- To spread Groq usage, each teammate can use their own key and run a subset:
  `python evaluate.py --only A1 A2 A3`.

## Code map

| File | Owner | What it does |
|---|---|---|
| `i_agent/schemas.py` | team | Data contracts: `Belief`, `ProvenanceRecord`, `SensorReading`, `ToolResult` |
| `i_agent/declarative.py` | Siddh | Belief graph, provenance log, weighted confidence, snapshots and diffs |
| `i_agent/tools.py` | Rudraksh | Tool schemas the LLM sees, and safe execution |
| `i_agent/procedural.py` | Rudraksh | ReAct loop, LLM client, retries, no-tools baseline |
| `i_agent/prompts/system.md` | Rudraksh | The epistemic rules given to the LLM |
| `i_agent/sensorimotor.py` | Udit | Mock environment: LiDAR, camera with lighting, motion |
| `i_agent/scenario.py` | Udit | Builds the three layers from a scenario file |
| `i_agent/evaluation.py` | Udit | Automatic checks: answer, tools, memory, grounding |
| `i_agent/prompts/system_sensors.md` | Rudraksh | Prompt for the "sensors" ablation level (no memory tools) |
| `scenarios/dev/*.json` | all | The 15 development scenarios (the project's data) |
| `scenarios/heldout/*.json` | all | Held-out set 1: 10 scenarios, frozen 5 Oct before any run (`FROZEN.md`) |
| `scenarios/heldout2/*.json` | all | Held-out set 2: 11 scenarios, frozen 18 Oct before any run (`FROZEN.md`) |
| `run_scenario.py` | Udit | Demo script with the printed trace; `--level` switches parts off |
| `evaluate.py` | Udit | Test suite runner: `--set`, `--level`, `--temperature`, `--rescore` |
| `run_experiments.py` | Udit | Runs every set x level combination in priority order |
| `report.py` | Udit | Pools all runs into tables, an ablation chart and a hand-review sheet |
| `server.py` | team | Web UI backend (FastAPI): sessions, streamed agent steps, log replay |
| `i_agent/replay.py` | team | Snapshots of all three layers after each step; rebuilds logged runs step by step |
| `web/` | team | React frontend (Vite); `web/dist` is the built app that `server.py` serves |

## Key design decisions

- **Perspectives.** Every belief carries a perspective: `self`, `map`, `user` or `agent:<id>`.
  They sit side by side in the graph (edge key `predicate|perspective`), so "what the user thinks",
  "what I see" and "what the records say" never overwrite one another.
- **Weighted confidence** (in `declarative.py`, v4; replaces the earlier fixed ×0.3).
  - *Evidence.* Every live reading updates the static map's belief about the same fact by Bayes'
    rule in log-odds, weighted by the sensor's reliability r (LiDAR 0.95, camera 0.95 or 0.82 in dim
    or yellow light, bumper and odometry 0.99): odds × r/(1−r) if the reading agrees, ÷ if it
    contradicts, kept within 0.01–0.99. For a map that says "clear" (0.99), one "blocked" reading
    gives 0.84 and a second gives 0.21; a spike followed by a "clear" reading returns it to 0.99.
    Each change is logged with the sensor, its reliability and the old and new confidence.
  - *Age.* Records are compared by confidence × 0.5^(age / half-life): 30 min for the robot's own
    sensor-based beliefs, 2 h for other robots' reports, 7 days for the map. `query_beliefs` returns
    this as `weighted_confidence`, and disagreements name the most trusted record. bot_02's
    1-hour-old 0.9 counts as 0.64 against bot_03's 10-minute-old 0.85 at 0.80.
  - Only the map is ever updated automatically. User and other-robot beliefs are other minds' views
    and are kept as they are; the user's beliefs do not decay, since they are a record of what the
    user thinks, not evidence about the world.
  - In dim or yellow light, a camera that does not see an object counts as unconfirmed until a second
    look agrees, as a single LiDAR reading does.
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

### Ablation levels: what does each part add?

Each level adds one part of the architecture to the one before it, using the same model and prompt rules:

| Level | What the agent has |
|---|---|
| `baseline` | No tools. Starting memory pasted into the prompt as text. |
| `sensors` | Sensor tools only, memory as text. A plain tool-using agent with no memory layer: the **fair baseline**. |
| `plain` | All 8 tools including the memory layer (graph, provenance, weighted confidence), but no safeguards. |
| `checks` | + tool-layer checks: memory check on sensor readings, grounded writes, disagreement summary, safe moves. |
| `full` | + the answer self-check. The complete system. |

Argument repair and parsing of text-written tool calls are on at every level: they fix formatting, not reasoning.

Levels without memory tools (`baseline`, `sensors`) cannot pass the tool or memory checks by design,
so **compare levels on the "correct answer" rate** (every answer check passed). `report.py` reports both.

### Dev set vs held-out sets

All safeguards were added after watching failures on the **dev** scenarios, so dev results are
optimistic. Held-out scenarios are written separately and frozen before the agent ever runs on them:
their SHA-256 hashes are in `FROZEN.md`, a test fails if any file changes, and the git commit that
froze them predates every result on them.

- **Held-out set 1** (`scenarios/heldout/`, frozen 5 Oct) was run on the mid-semester system (v1).
  Its results were known while v2 was built, so under v2 it is no longer a clean test. It is still
  run and reported, separately.
- **Held-out set 2** (`scenarios/heldout2/`, frozen 18 Oct) was written and frozen after the v2
  dev fixes had started but before any run on it. Its **v2** result is the clean generalisation
  number: **27/33 correct answers (82%), 25/33 all checks**, with NA4, NP1 and NP2 failing.
  Those failures were then used to build **v3**, so v3 results on held-out set 2 are no longer a
  clean test; they are reported separately and labelled as such.

Caveat: the system and both held-out sets were written with the same AI coding assistant, so the
tests are not fully independent. In particular, two more rounds of dev-set fixes were made after
held-out set 2 was frozen, by an author who knew its contents (though not its results). Scenarios written by teammates who have not read the code would be
a stronger test.

### System versions

Every log records the system version (`SYSTEM_VERSION` in `i_agent/__init__.py`), and `report.py`
never pools results across versions. **v1** is the mid-semester system (6 Oct). **v2** (18 Oct) adds
the safeguards marked *(v2)* in "Explaining your part" below; each was added after a dev-set failure.
**v3** (19 Oct) fixes the causes of the remaining failures on every set, including held-out set 2:
self-check messages give the exact tool call to make (the small model kept announcing
`update_belief` instead of calling it), a question about "your route" requires a scan of the
planned route from memory, an answer that says "another robot" must name it and its age,
`get_provenance` with a wrong property shows the entity's whole history, and a LiDAR scan in a
direction with no route names the routes that exist, `record_user_belief` only stores values the
user actually said (the model had stored another robot's report as the user's belief), and the
self-check gives the exact `record_user_belief` call built from the user's words. Each fix is general
(no scenario ids or answers are hard-coded) and has a unit test on a dev scenario. v3 results use
`qwen2.5:7b-8k` (same weights, 8192-token context; see "Models and limits").
**v4** (18 Nov) replaces the fixed ×0.3 map downgrade with weighted confidence (see "Key design
decisions"), at the course instructor's suggestion. It was not tuned on any scenario's results.

### Repeats and temperature

At temperature 0 the local model is nearly deterministic: repeated runs often give word-for-word
identical answers, so they measure reproducibility rather than spread. `run_experiments.py`
therefore also repeats the full system at temperature 0.7. Results show 95% confidence intervals
(Wilson) over the pooled runs.

### Checking the checks

Keyword checks can misjudge paraphrases. `results/review.html` lists answers next to their
automatic verdict so a person can mark agree / disagree; report the agreement rate alongside results.

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
| A6_scan_before_driving | Asked to drive; must scan first and refuse to drive into the obstacle |
| A7_report_vs_camera | Another robot's report says the box is here; the camera does not see it |
| B4_user_insists | User says "I painted it red, store that"; camera and log say blue |
| H2_unknown_room | Asked what is in a room no sensor or record covers |
| P2_why_downgraded | Two turns: finds the route blocked, then explains from the log why the map lost confidence |

Held-out set 1 (`scenarios/heldout/`): HA1 route to the right blocked · HA2 route to the left reopened ·
HA3 noisy scan to the left · HA4 crate missing in a dim room · HA5 crate found in a different room
than the map says · HB1 white / dark green / green cup under dim light · HB2 keys moved (false belief) ·
HB3 three robots disagree · HH1 unknown property (weight) · HP1 provenance including the reason.

Held-out set 2 (`scenarios/heldout2/`): NA1 route behind the robot blocked · NA2 asked to go along a
route the map says is blocked but is clear · NA3 a spurious "clear" reading on a blocked route ·
NA4 another robot's report vs the camera in dim light · NB1 user insists a white cup is green ·
NB2 laptop moved (false belief) · NB3 two robots disagree about a location · NH1 a report that does not
exist · NH2 colour of an object in another room · NP1 who, when and why a door was locked ·
NP2 two turns: route blocked, then why the map entry changed.

## Explaining your part (for the evaluation)

**Siddh (memory, `declarative.py`).** Beliefs are edges in a NetworkX MultiDiGraph keyed by
`predicate|perspective`, so the map's, the user's and other robots' views of the same fact coexist.
Every write goes through `_write()`, which also inserts a provenance row into SQLite.
`update_with_evidence()` weighs each live sensor reading against the static map (Bayes' rule in
log-odds, by the sensor's reliability) and `weighted_confidence()` discounts a record by its age when
records are compared (see "Weighted confidence" above). User and other-robot beliefs are never
changed automatically, because they are other minds' views.
`snapshot()` and `diff()` store the epistemic state as a sequence of graphs.

**Rudraksh (LLM, `procedural.py`, `tools.py`, `prompts/system.md`).** A hand-written ReAct loop over the
OpenAI-compatible API (Groq or Ollama). Tools are the only path to the other layers. Safeguards, each added
after a failure we actually observed in the logs:
1. **Memory check on every sensor reading.** Sensor results carry a `memory_check` listing the stored
   beliefs the reading contradicts, so the conflict cannot be overlooked.
2. **Grounded writes.** `update_belief` refuses any value that never appeared in a tool result. We saw a
   model invent "the map says red" and write it into memory; now that is impossible. *(v2)* It also
   refuses a `self` belief whose source is not one of the robot's own sensors (B3: the model copied
   bot_03's report into its own belief), a belief about an entity no sensor or memory record mentions
   (H1), and a sensor-sourced value that sensor never reported (the model wrote "blue, source camera"
   when the camera had seen nothing).
3. *(v2)* **Safe moves.** `move` is refused unless a LiDAR scan of that route in the current turn said
   clear (A6: the model tried to drive before scanning).
4. **Answer self-check** (`check_answer`), which sends a draft answer back to the LLM (up to 6 times; 4 before v4) if:
   - it never called `query_beliefs` (the message names the exact call to make),
   - it claims "I updated my belief" without calling `update_belief`,
   - it announces an action ("I will check…") without doing it,
   - a sensor-vs-memory conflict is still unresolved,
   - it relies on the static map for something a sensor could check right now,
   - it gives properties to an entity no tool returned (e.g. calling `crate_07` blue because `box_01` is),
   - the user stated a belief ("I left the box in…") that was never recorded,
   - *(v2)* records about a named entity disagree and the answer leaves one out (B3),
   - *(v2)* memory holds records about a named entity that the agent never looked at (B1),
   - *(v2)* it names a colour that no tool result or user message contains,
   - *(v2)* it claims a belief was downgraded when nothing was (B4),
   - *(v2)* it does not mention the user belief it just recorded (B4),
   - *(v2)* the user asks why / who / when and `get_provenance` was not called this turn (P2).
5. **Small-model tolerance.** Plain parameter names (`entity`, `property`, `value`), alias mapping,
   tool calls written as text are parsed and executed *(v2: also JSON blocks and Python-style calls such
   as `query_beliefs(entity="box_01")`)*, and malformed calls are retried with the API's error message.

`python evaluate.py --level checks` switches item 4 off, and `--level plain` switches items 1–4 off,
which measures how much they contribute.

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
- **Changes on 18 Oct (v2), all from dev-set results:** answer checks now accept a plain inflection
  of a phrase ("not detect" matches "not detected", "hour" matches "hours"; "red" still never
  matches "reduced"), because correct answers in A7 were marked wrong. H2 also accepts "cannot
  confirm". `tools_forbidden` counts only calls the tool layer executed, since a refused call has no
  effect. These apply to every set; held-out files themselves were never edited.
- **Checker fix (19 Oct).** The inflection tolerance above was also applied to forbidden phrases, so
  a correct answer ("I will not proceed until the path is cleared") failed `answer_excludes: "path
  is clear"`. Forbidden phrases now match exactly; saved logs were re-scored with `--rescore`.
- **Tightened checks (5 Oct).** A2–A5 accepted words that also match wrong answers ("clear" inside
  "not clear", or bare "no" / "not"). They now require specific phrases and reject negations; all saved
  logs were re-scored with `--rescore`.
- **Sample size.** Results so far are 1 run per scenario on `qwen2.5:7b`. LLM output varies between runs,
  so report pass rates over 5 runs (`python evaluate.py --provider ollama --model qwen2.5:7b`) before
  drawing conclusions.
- **Development history.** `logs/dev_iterations/` keeps the earlier runs, from before each safeguard was
  added. They show which failures each safeguard fixed, which is useful for the report.
