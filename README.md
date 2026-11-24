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

The current code declares **system version v4** (`i_agent/__init__.py`). Its confidence model updates static-map beliefs using sensor reliability and compares records using age-discounted confidence. User beliefs and reports from other robots remain distinct from the agent's own observations.

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

Scenario definitions are in `scenarios/dev/`, `scenarios/heldout/`, and `scenarios/heldout2/`.

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
python report.py
```

Results and visualizations can be generated in `results/`; raw per-run JSON records, if retained, are stored in `logs/`. The `report.py` script aggregates experimental records across configurations and versions.

### Interpreting results

The recorded **v2** evaluation on held-out set 2 produced **27/33 correct answers** and **25/33 runs passing all checks** (`logs/20261018-210452_heldout2_full_qwen2.5-7b/`). Later changes were informed by some of those failures, so subsequent results on that set should not be treated as independent held-out estimates.

The final **v4** implementation has unit-test coverage and includes weighted-confidence updates, but a complete v4 LLM benchmark is not included with this project snapshot. Older v2/v3 figures should not be interpreted as v4 performance. Automatically scored answers may also require manual review.

For comparisons with tool-free baselines, use **correct-answer rate** rather than overall pass rate: the latter includes tool and memory checks that a tool-free baseline cannot satisfy by design.

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
| `report.py` | Evaluation summaries and visualizations |
| `server.py` | FastAPI backend and frontend server |
| `web/` | React application |
| `scenarios/` | Development and held-out scenario definitions |
| `tests/` | Automated tests |

## Team

| Member | Student ID | Primary contribution |
|---|---|---|
| Siddh Jain | 2024ADPS0837G | Declarative memory, belief graph, confidence and provenance |
| Rudraksh Kumar | 2024ADPS0820G | Procedural LLM controller, tools and answer safeguards |
| Udit Chaudhary | 2024A7PS0618G | Simulated environment, scenarios, evaluation and experimental analysis |

## Limitations

The environment and sensors are simulated rather than physical. LLM responses depend on model behavior, and keyword-based automatic checks can accept or reject responses incorrectly. Held-out evaluation is most informative when the tested scenarios have not influenced subsequent development. The repository therefore separates system versions in its evaluation records.

This README documents the implementation and how to reproduce its operation; the course report contains the full project analysis and required generative-AI disclosure.
