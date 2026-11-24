# I, Agent

**A three-layer architecture for grounded language-model agents**  
CS F407 — Artificial Intelligence | BITS Pilani, K. K. Birla Goa Campus

I, Agent combines structured memory, language-model reasoning, and a simulated environment to investigate how an agent can reconcile prior beliefs with new observations. The system records where information originated, distinguishes different observers' perspectives, and checks actions and answers against available evidence.

## Architecture

```text
                 User question
                       |
                       v
       +--------------------------------+
       | Procedural layer               |
       | LLM controller and tool calls  |
       | i_agent/procedural.py, tools.py|
       +--------------------------------+
                  /             \
                 v               v
   +--------------------+   +---------------------+
   | Declarative memory |   | Sensorimotor layer  |
   | NetworkX graph     |   | Simulated world      |
   | SQLite provenance  |   | LiDAR, camera, motion|
   | declarative.py     |   | sensorimotor.py      |
   +--------------------+   +---------------------+
                 \               /
                  v             v
             Grounded response
```

- **Declarative memory:** Stores beliefs as graph edges with values, confidence, source and perspective (`self`, `map`, `user`, or `agent:<id>`). SQLite records changes and their provenance. Snapshots and diffs expose how memory changes over a run.
- **Procedural reasoning:** Uses a tool-calling ReAct loop with an OpenAI-compatible model provider. The controller queries memory, invokes simulated sensors, checks proposed memory updates, and produces answers based on retrieved evidence.
- **Sensorimotor simulation:** Models routes, obstacles, objects, lighting and sensor observations. LiDAR, camera and motion tools provide observations that may agree or conflict with stored information.

The current code declares **system version v4.1** (`i_agent/__init__.py`). Its confidence model updates static-map beliefs using sensor reliability and compares records using age-discounted confidence. User beliefs and reports from other robots remain distinct from the agent's own observations. **The final system passes every check on all 46 test scenarios** (see [Results](#results)).

Reports: the course report `I_Agent_Final_Project_Report_Updated.pdf` and the architecture verification report `docs/Architecture_Verification_Report.pdf` (source in `.md` next to it).

## Requirements

- Python 3.10+ and `pip`
- An LLM provider: [Ollama](https://ollama.com/) for local inference, or a Groq API key
- Node.js and npm only if you need to rebuild the React frontend

Install Python dependencies from the project root:

```bash
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

Then install dependencies:

```bash
pip install -r requirements.txt
```

### Option A: Ollama (local)

Start Ollama, then create the project's 8K-context model:

```bash
ollama pull qwen2.5:7b
ollama create qwen2.5:7b-8k -f ollama/Modelfile
```

Run the browser-based application:

```bash
python server.py --provider ollama --model qwen2.5:7b-8k
```

Open **http://localhost:8000**.

### Option B: Groq API

Copy `.env.example` to `.env` and set `GROQ_API_KEY` to your own key. Do not commit `.env` or credentials.

```bash
python server.py --provider groq --model openai/gpt-oss-20b
```

The command-line scenario and evaluation tools also accept `--provider` and `--model` arguments.

## Running scenarios

```bash
python run_scenario.py --list
python run_scenario.py A1 --provider ollama --model qwen2.5:7b-8k
python run_scenario.py B1 --provider ollama --model qwen2.5:7b-8k
python run_scenario.py A1 --level plain --provider ollama --model qwen2.5:7b-8k
```

Two central scenarios are:

- **Scenario A — conflicting route information:** The stored map describes a clear route, while the LiDAR sensor detects an obstruction. The agent must consider live evidence and update or qualify its stored belief.
- **Scenario B — different perspectives:** The user, camera and other stored reports may give different descriptions of an object. The agent must retain each perspective and avoid treating them as the same observation.

Scenario definitions are in `scenarios/dev/` (15), `scenarios/heldout/` (10), `scenarios/heldout2/` (11) and `scenarios/heldout3/` (10). Each held-out set was frozen before any run on it: `FROZEN.md` in each folder lists every file's SHA-256, and a test fails if one changes. Held-out set 3 was written by a separate AI agent that was given only `scenarios/TEMPLATE.md` (how to write a scenario without reading the code), never the code itself. To add a set, follow `TEMPLATE.md` and freeze it with `python scenarios/freeze.py <set>`.

## Web interface

`server.py` hosts the Python backend and serves the React application from `web/dist` when that directory exists. The interface provides:

- A live session view with the simulated world, tool calls, memory graph, provenance records and a timeline of agent steps.
- A replay view for saved JSON evaluation logs, when those logs are present locally.

To rebuild the frontend:

```bash
cd web
npm install
npm run build
```

Then restart `python server.py` from the project root. For frontend development, use `npm run dev` in `web/` while the backend is running.

## Evaluation

The evaluation framework checks the agent's output and intermediate behavior along four dimensions:

| Check | Description |
|---|---|
| Answer | Required information is present in the final response |
| Tools | Required evidence-gathering tools were invoked |
| Memory | The final belief state meets scenario expectations |
| Grounding | Answered facts are supported by available evidence |

Five ablation configurations are supported:

| Level | Configuration |
|---|---|
| `baseline` | No tools; initial memory is included as text |
| `sensors` | Sensor tools with initial memory supplied as text |
| `plain` | All sensor and memory tools, without extra safeguards |
| `checks` | Tool-level consistency and safety checks, without answer self-check |
| `full` | Tool-level checks and answer self-check |

Example commands:

```bash
python -m pytest
python evaluate.py --set dev --level full --runs 1 --provider ollama --model qwen2.5:7b-8k
python evaluate.py --set heldout2 --level sensors --runs 1 --provider ollama --model qwen2.5:7b-8k
python evaluate.py --set heldout3 --level baseline --runs 1 --provider ollama --model qwen2.5:7b-8k
python run_experiments.py --plan v4fast   # full system + baseline on all four sets (about 1.5 h)
python report.py
```

After a code change, `python rerun_affected.py <log folders>` replays each saved run's trace through the
changed checks: runs on which no change would have fired are carried over (identical prompts at
temperature 0, marked `carried_over` with the source file) and only the others are run again.

Results and visualizations can be generated in `results/`; raw per-run JSON records, if retained, are stored in `logs/`. The `report.py` script aggregates experimental records across configurations and versions.

### Interpreting results

For comparisons with tool-free baselines, use **correct-answer rate** rather than overall pass rate: the latter includes tool and memory checks that a tool-free baseline cannot satisfy by design.

## Results

Final system **v4.1**, `qwen2.5:7b-8k` via Ollama (Q4_K_M) on a laptop RTX 3050 (4 GB), temperature 0,
one run per scenario. The full table with 95% Wilson intervals is in `results/results.md` (`python report.py`).

| Set | Scenarios | Full system: all checks | Text-only baseline: correct answer |
|---|---|---|---|
| Development | 15 | **15/15** | 5/15 |
| Held-out 1 | 10 | **10/10** | 5/10 |
| Held-out 2 | 11 | **11/11** | 5/11 |
| Held-out 3 (written without the code) | 10 | **10/10** | 3/10 |
| **Total** | **46** | **46/46** | 18/46 (39%) |

The baseline's typical failure is the one the project targets: asked whether its route is clear, it
trusts the day-old map and says yes.

**Clean generalisation result.** On held-out set 2 with system v2, measured before any change was made
because of it, the full system answered 27/33 correctly (82%) against 5/11 (45%) for the text-only
baseline, and answers that also passed the tool and memory checks went from 0% to 76% (25/33).

**From v4 to v4.1.** The first v4 pass scored 13/15, 9/10 and 11/11 on the first three sets; on held-out
set 3, IX6 failed and IX7 stalled. Each cause was fixed with a general rule and a unit test: the system
records a belief the user states unambiguously (the model kept claiming it had), and the self-check
sends back answers that say what is in a room nothing has seen, report a colour seen under yellow or
dim light as fact, or pick between two robots' reports about a route without scanning it. Replies are
capped at 1024 tokens. Because these fixes followed failures on held-out sets 1 and 3, the v4.1 results
on those sets are reported as seen, not as clean tests.

| Log folder (`logs/`) | Contents |
|---|---|
| `20261124-232701_dev_full_qwen2.5-7b-8k/` | development set, v4.1 (3 run again, 12 carried over) |
| `20261124-233736_heldout_full_qwen2.5-7b-8k/` | held-out 1, v4.1 (2 run again, 8 carried over) |
| `20261124-234256_heldout2_full_qwen2.5-7b-8k/` | held-out 2, v4.1 (1 run again, 10 carried over) |
| `20261124-234450_heldout3_full_qwen2.5-7b-8k/` | held-out 3, v4.1 (5 run again, 5 carried over) |
| `20261125-*_baseline_qwen2.5-7b-8k/` | text-only baseline on each set |
| `20261124-{214502,221252,223612,230004}_*` | the original v4 passes the carried-over runs come from |
| `dev_iterations/20261118-145103_dev_full_qwen2.5-7b-8k/` | the A1 and B1 runs shown in the video and the replay view |

Replay any of them in the web interface: `http://localhost:8000/#replay=<log file path>&step=1`.

## Main files

| Path | Purpose |
|---|---|
| `i_agent/declarative.py` | Belief graph, confidence updates, provenance and snapshots |
| `i_agent/procedural.py` | LLM orchestration and reasoning loop |
| `i_agent/tools.py` | Tool definitions, validation and execution |
| `i_agent/sensorimotor.py` | Simulated environment and sensor behavior |
| `i_agent/scenario.py` | Scenario loading and world construction |
| `i_agent/evaluation.py` | Automated scenario checks and ablation configuration |
| `i_agent/replay.py` | Step-by-step reconstruction of recorded runs |
| `run_scenario.py` | Command-line scenario runner |
| `evaluate.py` | Evaluation runner |
| `run_experiments.py` | Experiment matrix runner |
| `rerun_affected.py` | Brings saved runs up to a new system version, rerunning only the runs a change affects |
| `report.py` | Evaluation summaries and visualizations |
| `server.py` | FastAPI backend and frontend server |
| `web/` | React application |
| `scenarios/` | Development and held-out scenario definitions; `TEMPLATE.md` guide, `freeze.py` |
| `docs/` | Architecture verification report |
| `tests/` | Automated tests |

## Team

| Member | Student ID | Primary contribution |
|---|---|---|
| Siddh Jain | 2024ADPS0837G | Declarative memory, belief graph, confidence and provenance |
| Rudraksh Kumar | 2024ADPS0820G | Procedural LLM controller, tools and answer safeguards |
| Udit Chaudhary | 2024A7PS0618G | Simulated environment, scenarios, evaluation and experimental analysis |

## Limitations

The environment and sensors are simulated rather than physical. LLM responses depend on model behavior, and keyword-based automatic checks can accept or reject responses incorrectly (`results/review.html` supports a manual audit). Each final result is a single run at temperature 0, so it shows reproducible behaviour rather than variability. Held-out evaluation is most informative when the tested scenarios have not influenced subsequent development. The repository therefore separates system versions in its evaluation records.

This README documents the implementation and how to reproduce its operation; the course report contains the full project analysis and required generative-AI disclosure.
