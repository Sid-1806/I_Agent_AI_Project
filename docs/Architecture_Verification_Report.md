# I, Agent: Architecture Verification Report

Team Null Pointers: Siddh (memory layer), Rudraksh (procedural layer), Udit (world and evaluation).
System version v4.1 (`SYSTEM_VERSION` in `i_agent/__init__.py`), model qwen2.5:7b with an 8k context, run locally with Ollama.

This report explains the structural prompts the agent works under, traces how information passes
through the three layers, and sets out how the system keeps the language model from stating facts
that are not in its memory or its sensor readings. Section 6 gives the evidence that it works and
Section 7 its limits.

## 1. The three layers and their boundaries

| Layer | Module | Holds | Reached by |
|---|---|---|---|
| Declarative (memory) | `i_agent/declarative.py` | Belief graph (NetworkX `MultiDiGraph`), provenance log and snapshots (SQLite) | `query_beliefs`, `get_provenance`, `update_belief`, `record_user_belief` |
| Procedural (brain) | `i_agent/procedural.py`, `i_agent/tools.py` | The LLM in a hand-written ReAct loop, the 8 tools, the answer self-check | the user's question |
| Sensorimotor (world) | `i_agent/sensorimotor.py` | The mock world's ground truth: rooms, routes, obstacles, objects, lighting | `read_lidar`, `read_camera`, `get_pose`, `move` |

The LLM never sees memory or the world directly. Every fact reaches it as a JSON tool result,
produced by Python code it cannot change. This is the property everything else builds on: each
claim in an answer can be traced to a specific tool result in the run's log.

A belief is one edge of the graph, `subject --predicate--> object`, with five attributes:
perspective (`self`, `map`, `user` or `agent:<id>`), source, confidence, timestamp, and the edge key
`predicate|perspective`. Because the key includes the perspective, the map's, the user's, other
robots' and the robot's own view of the same fact sit side by side and never overwrite each other.
Every write goes through one function (`_write`) that also inserts a provenance row: old and new
value, old and new confidence, source, time and reason.

## 2. Structural prompts

### 2.1 System prompt (`i_agent/prompts/system.md`)

The prompt first tells the model what it is: "the reasoning layer of a mobile robot. You cannot see
the world or your memory directly. You learn things ONLY by calling tools." It then lists eight rules:

1. **Grounding.** Every fact in the answer must come from a tool result in this conversation; if
   neither memory nor sensors know, say so.
2. **Check before you answer.** For the current physical state, check memory, then a live sensor;
   never drive a route to find out whether it is clear.
3. **Conflict rule.** For the current state: live sensor > recent report from another robot >
   static map. Record a sensor observation with `update_belief`; each reading also updates the
   map's confidence automatically (Section 4).
4. **Noisy sensors.** If one reading sharply contradicts memory, read again before updating.
5. **Perspectives.** Keep user, self, map and other robots apart; record the user's view with
   `record_user_belief`; do not overwrite another robot's record with a distorted perception.
6. **Disagreeing records.** Report each with source and age, and trust the one with the higher
   age-weighted confidence.
7. **Provenance.** For where/when/why questions, call `get_provenance` and cite source, reason and age.
8. **Answer style.** Answer directly, say which layer each fact came from.

### 2.2 Tool schemas (`TOOL_SCHEMAS` in `i_agent/tools.py`)

Each of the 8 tools has an OpenAI-style function schema whose description names the layer it reaches
("MEMORY (declarative layer)", "SENSOR (sensorimotor layer)"). Parameters use plain words (`entity`,
`property`, `value`) because the 7B model confused the graph terms subject/predicate/object; aliases
are mapped back. `query_beliefs` always returns every perspective and, when records disagree,
lists them newest first with the most trusted one named.

### 2.3 Prompts generated at run time

Two kinds of text are added to the conversation by code, not written by hand per scenario:

- **Tool-result hints.** A LiDAR reading that contradicts memory carries a `memory_check` naming the
  stored belief it contradicts and what to do ("Single reading: read once more", or the exact
  `update_belief(...)` call once two readings agree). A reading in a direction with no route lists the
  routes that do exist. A contradicted map belief comes with a one-sentence summary of its new
  confidence.
- **Self-check messages** (Section 5.2), each naming the exact tool call to make where one is needed,
  for example `read_lidar(direction="front")`, because the small model often announced a call
  instead of making it. Tool calls the model writes as JSON or Python-style text are parsed and run.

## 3. How information passes through the layers: a traced run

Scenario A1 (dev set), system v4, log `logs/dev_iterations/20261118-145103_dev_full_qwen2.5-7b-8k/A1_route_blocked_run1.json`.
Memory at the start: the robot's planned route is `route_A`; the static map (one day old, confidence
1.0) says `route_A` is clear. Ground truth in the world: an obstacle 12 cm along `route_A`.

| Step | Layer crossed | What happened |
|---|---|---|
| 1 | user → brain | "Is your route clear? Justify your response by inspecting your internal system layers." |
| 2 | brain → world → memory | `read_lidar(front)` returns `route_A: 12 cm, blocked`. The tool layer compares it with memory (`memory_check`: map says clear) and the memory layer weighs it as evidence: map confidence 1.0 → **0.839**, logged with the sensor and its reliability. |
| 3–4 | brain → self-check | The draft answers from one reading. The self-check rejects it: unconfirmed conflict, read again (exact call given). |
| 5–6 | brain → memory, world | `query_beliefs` and `get_pose`. |
| 7–8 | brain → self-check | A second draft is rejected for the same reason. |
| 9 | brain → world → memory | Second `read_lidar(front)`: still 12 cm, blocked. Map confidence 0.839 → **0.215**. The conflict is now confirmed. |
| 10–11 | self-check → brain | The draft is rejected until the observation is recorded: the message gives `update_belief(entity="route_A", property="status", value="blocked", source="lidar_front", ...)`. |
| 12 | brain → memory | `update_belief` is accepted (the value matches what the LiDAR reported) and writes the robot's own belief `route_A.status = blocked` (self, lidar_front). The map belief stays, with its lowered confidence and full history. |
| 13 | brain → user | "No, your route is not clear. The front lidar sensor confirmed that there is an object blocking route_A, and my belief has been updated accordingly." All six automatic checks pass. |

Every number and claim in the answer appears in a tool result above it. The web UI's Replay screen
(`python server.py`, then `#replay=<log>&step=<n>`) rebuilds this run step by step from the log and
shows the world, the agent's steps and the belief graph at each step.

## 4. Weighted confidence (v4)

**Evidence.** Each live reading is evidence about the static map's belief for the same fact. The
memory layer updates that belief's confidence by Bayes' rule in log-odds:

    odds_new = odds_old × r / (1 − r)   if the reading agrees,   odds_old × (1 − r) / r   if it contradicts

where r is the sensor's reliability (LiDAR 0.95; camera 0.95, or 0.82 in dim or yellow light; bumper
and odometry 0.99). Confidence stays within 0.01–0.99, agreement never lowers it and contradiction
never raises it. One reading moves a confident map a little (0.99 → 0.84); two agreeing readings move
it a lot (→ 0.21); a spurious reading followed by a normal one is undone. Only the map is updated
automatically: the user's and other robots' beliefs are other minds' views and are kept as they are.

**Age.** When records are compared, each counts with confidence × 0.5^(age / half-life): 30 minutes
for the robot's own sensor beliefs, 2 hours for other robots' reports, 7 days for the map; the user's
beliefs do not decay, because they record what the user thinks, not evidence about the world.
`query_beliefs` returns this `weighted_confidence`; for B3, bot_02's hour-old report (0.9) counts as
0.64 against bot_03's ten-minute-old one (0.85) at 0.80, so the newer report is trusted.

This replaced the earlier fixed rule (map confidence × 0.3 whenever the agent wrote a contradicting
belief), which treated one reading the same as many and ignored how old a record was.

## 5. How the system avoids hallucinating facts

The guarantees come in three rings, from hardest to softest.

### 5.1 What memory will accept (enforced in code, `tools.py`)

- **Grounded writes.** `update_belief` refuses a value that never appeared in a tool result, a
  belief about an entity no sensor or memory record mentions, a source that is not one of the
  robot's own sensors, and a value that the named sensor did not report. The model once wrote
  "blue, source camera" when the camera had seen nothing; that write is now impossible.
- **User beliefs.** `record_user_belief` stores only values the user actually said, so another
  robot's report can never be filed as the user's view.
- **Safe moves.** `move` is refused unless a LiDAR scan this turn showed the route clear.
- **Unconfirmed readings.** A single contradicting reading stays open until a second reading
  confirms it, even if the model writes a belief in between.

Because memory rejects these writes, an invented fact cannot persist into later turns even if the
model states it once.

### 5.2 What an answer must satisfy (the self-check, `check_answer` in `procedural.py`)

Before an answer is accepted it is compared with what actually happened in the layers. It is sent
back (up to 6 times, within 16 steps) if, among others:

- memory was never queried, or an entity it names has records it never looked at;
- it names an entity no tool returned, or a colour no tool result or user message contains;
- it claims a camera or LiDAR showed something without that sensor being called;
- it claims an update that was never made (or was refused), or a downgrade that did not happen;
- a sensor-versus-memory conflict is unresolved, or a single reading is unconfirmed;
- records disagree and the answer leaves one out, or a contradicted robot report is not named;
- the map's confidence was lowered this turn and the answer does not say so;
- the user's stated belief was not recorded, or was recorded but not reported back;
- a why/who/when question was answered without the provenance log, or without the logged reason;
- it announces an action instead of taking it, or does not answer a yes/no question directly;
- (v4.1) robots disagree about a route the robot faces and no LiDAR reading of it was taken;
- (v4.1) it reports a colour seen under yellow or dim light without the lighting and the other
  recorded colours;
- (v4.1) it says what is in a room that nothing has seen ("no objects in Room 309").

(v4.1) When the user's own words fully determine their belief ("I left box_01 in Room 101"), the
system records it as the user's view itself, logged as an automatic step: the 7B model repeatedly
wrote "I have recorded it" without calling the tool. Replies are capped at 1024 tokens.

Every rule is general: none names a scenario, entity or expected answer. Each was added after a
failure observed in a log, and each has a unit test on a development scenario.

### 5.3 What the evaluation checks afterwards (`evaluation.py`)

Each run is scored on four kinds of check: the answer's content, the tools actually called, the final
state of the belief graph, and grounding (no value word in the answer that is absent from every
tool result and user message). A run passes only if all pass. Required phrases accept word forms
("blocks" for "blocked"); forbidden phrases match exactly.

## 6. Verification evidence

- **109 unit tests** (`python -m pytest`, no LLM needed) cover the memory layer, every tool safeguard,
  every self-check rule, the scenario files, and an exact replay of a logged run.
- **46 scenarios** in four sets. 15 development scenarios were used to build the system. Three held-out
  sets were written and frozen (SHA-256 hashes in `FROZEN.md`, checked by a test) before the agent
  ran on them: set 1 (10 scenarios, 5 Oct), set 2 (11 scenarios, 18 Oct) and set 3 (10 scenarios,
  24 Nov), which a separate AI agent wrote from `scenarios/TEMPLATE.md` alone, without the code.
- **Clean generalisation result** (held-out set 2 on system v2, before any change was made because of
  it): the full system answered **27 of 33** runs correctly (82%) against **5 of 11** (45%) for the same
  model with its memory pasted into the prompt and no tools; answers that were also backed by real
  tool calls and memory went from **0%** to **76%**.
- **Ablation** (each level adds one part of the architecture, same model): see `results/results.md`
  for every level and set, with 95% Wilson intervals.
- **Final system (v4.1)**, one run per scenario at temperature 0:

  | Set | Full system: all checks | Text-only baseline: correct answer |
  |---|---|---|
  | Dev | 15/15 | 5/15 |
  | Held-out 1 | 10/10 | 5/10 |
  | Held-out 2 | 11/11 | 5/11 |
  | Held-out 3 | 10/10 | 3/10 |
  | **Total** | **46/46** | **18/46** |

  The first v4 pass scored 13/15, 9/10 and 11/11 on the first three sets, with IX6 failing and IX7
  stalling on set 3. Each cause was fixed by a general rule (Section 5.2); saved runs on which no
  change would have fired were carried over (identical prompts at temperature 0) and the other 12
  were run again (`rerun_affected.py`).

Held-out set 2's failures were used to build v3, held-out set 1's to build v2, and held-out sets 1
and 3's v4 failures to build v4.1, so later results on those sets are reported as seen, not as clean
tests. The clean generalisation number is held-out set 2 on v2.

## 7. Limitations

- The model is a 7B model running on a laptop GPU; it needs many self-check rounds, and some answers
  stay clumsy even when they pass (for example, reporting the three colours in B1 but saying it trusts
  the distorted camera reading more).
- The world is simulated and discrete (rooms and routes); sensor noise is scripted.
- The system and held-out sets 1 and 2 were written by the same team, so those sets are not fully
  independent. Held-out set 3 was written without the code, but by an AI agent rather than a person.
- Each final result is a single run at temperature 0: it shows reproducible behaviour, not variability.
- Keyword-based answer checks can misjudge paraphrases; `results/review.html` lets a person check
  the automatic verdicts by hand.
- Confidence reliabilities and half-lives are set by hand, not calibrated on real sensors.
