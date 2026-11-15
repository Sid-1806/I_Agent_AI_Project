"""Web UI backend: talk to the agent and watch all three layers.

    python server.py                                  # local qwen2.5:7b via Ollama, http://localhost:8000
    python server.py --provider groq                  # Groq (needs GROQ_API_KEY in .env)
    python server.py --provider ollama --model llama3.1:8b

The React frontend in web/ is built into web/dist and served from here (build it once with
`npm install && npm run build` inside web/). During frontend development, run `npm run dev` in
web/ instead; it proxies /api to this server.

API
    GET  /api/config                     provider and model in use
    GET  /api/scenarios                  every scenario (dev and held-out), with its world and questions
    POST /api/sessions                   {"scenario": "A1", "level": "full"} -> a fresh world, memory and agent
    POST /api/sessions/{id}/ask          {"question": "..."} -> NDJSON stream, one frame per agent step
    GET  /api/sessions/{id}              every frame so far
    GET  /api/runs                       logged evaluation runs that can be replayed
    GET  /api/replay?file=logs/...json   a logged run rebuilt step by step

The server adds no logic of its own: it calls the same Agent, ToolRegistry, BeliefStore and MockEnv
as evaluate.py.
"""
from __future__ import annotations

import argparse
import json
import queue
import threading
import uuid
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from i_agent.evaluation import LEVELS, level_options
from i_agent.procedural import Agent, OpenAICompatibleLLM
from i_agent.replay import frame, replay, scenario_info
from i_agent.scenario import SETS, all_scenarios, build_world, load_scenario

ROOT = Path(__file__).parent
LOGS = ROOT / "logs"
DIST = ROOT / "web" / "dist"
LIVE_LEVELS = ["plain", "checks", "full"]

app = FastAPI(title="I, Agent")
LLM: OpenAICompatibleLLM | None = None
SESSIONS: dict[str, "Session"] = {}


class Session:
    def __init__(self, scenario: dict, level: str):
        tool_options, self_check = level_options(level)
        self.scenario, self.level = scenario, level
        self.world = build_world(scenario, **tool_options)
        self.agent = Agent(self.world.tools, LLM, self_check=self_check)
        self.turn = 0
        self.frames = [frame(self.world, 0, {"type": "start"})]
        self.lock = threading.Lock()


class NewSession(BaseModel):
    scenario: str
    level: str = "full"


class Question(BaseModel):
    question: str


@app.get("/api/config")
def config():
    return {"provider": LLM.provider, "model": LLM.model, "levels": {k: LEVELS[k] for k in LIVE_LEVELS}}


@app.get("/api/scenarios")
def scenarios():
    return [scenario_info(s) for set_name in SETS for s in all_scenarios(set_name)]


@app.post("/api/sessions")
def new_session(body: NewSession):
    if body.level not in LIVE_LEVELS:
        raise HTTPException(400, f"level must be one of {LIVE_LEVELS}")
    try:
        scenario = load_scenario(body.scenario)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e
    sid = uuid.uuid4().hex[:12]
    SESSIONS[sid] = s = Session(scenario, body.level)
    return {"session": sid, "scenario": scenario_info(scenario), "level": s.level, "frames": s.frames}


@app.get("/api/sessions/{sid}")
def get_session(sid: str):
    s = _session(sid)
    return {"session": sid, "scenario": scenario_info(s.scenario), "level": s.level, "frames": s.frames}


@app.post("/api/sessions/{sid}/ask")
def ask(sid: str, body: Question):
    s = _session(sid)
    question = body.question.strip()
    if not question:
        raise HTTPException(400, "empty question")
    if s.lock.locked():
        raise HTTPException(409, "the agent is still answering the previous question")
    events: queue.Queue = queue.Queue()

    def emit(f: dict) -> None:
        s.frames.append(f)
        events.put({"event": "frame", "frame": f})

    def work() -> None:
        with s.lock:
            try:
                s.turn += 1
                emit(frame(s.world, s.turn, {"type": "question", "text": question}))
                result = s.agent.ask(question, on_step=lambda step: emit(frame(s.world, s.turn, step)))
                events.put({"event": "done", "answer": result.answer})
            except Exception as e:  # noqa: BLE001 - report LLM/API failures to the page
                events.put({"event": "error", "message": f"{type(e).__name__}: {e}"})
            finally:
                events.put(None)

    threading.Thread(target=work, daemon=True).start()

    def stream():
        while (item := events.get()) is not None:
            yield json.dumps(item, ensure_ascii=False) + "\n"

    return StreamingResponse(stream(), media_type="application/x-ndjson")


@app.get("/api/results")
def results():
    """Evaluation summary for the results screen, from the same code as report.py."""
    import report
    report.LOGS = LOGS
    runs = report.load_runs()
    rows = report.summary_rows(report.group(runs))
    failing = [{"file": f"logs/{r['folder']}/{r['file']}", "scenario": r["scenario"], "set": r["set"],
                "system": r["system"], "level": r["level"], "model": r.get("model"), "folder": r["folder"],
                "answer_ok": r["answer_ok"],
                "failed": [f"{c['kind']}: {c['name']}" for c in r.get("checks", []) if not c["passed"]]}
               for r in runs if r["level"] == "full" and not r["passed"] and not r["errored"]]
    failing.sort(key=lambda f: f["folder"], reverse=True)
    folders: dict[str, dict] = {}
    for r in runs:
        f = folders.setdefault(r["folder"], {"folder": r["folder"], "set": r["set"], "level": r["level"],
                                             "system": r["system"], "model": r.get("model"),
                                             "temperature": r["temperature"], "runs": 0, "passed": 0})
        f["runs"] += 1
        f["passed"] += bool(r["passed"])
    return {"rows": rows, "failing": failing[:40],
            "folders": sorted(folders.values(), key=lambda f: f["folder"], reverse=True)}


@app.get("/api/runs")
def runs():
    out = []
    for folder in sorted(LOGS.glob("2*"), reverse=True):
        if not folder.is_dir():
            continue
        for f in sorted(folder.glob("*_run*.json")):
            head = json.loads(f.read_text(encoding="utf-8"))
            if head.get("mode") not in ("sensors", "plain", "checks", "full"):
                continue
            out.append({"file": f.relative_to(ROOT).as_posix(), "folder": folder.name,
                        "scenario": head["scenario"], "set": head.get("set", "dev"), "level": head["mode"],
                        "system": head.get("system", "v1"), "passed": head.get("passed")})
    return out


@app.get("/api/replay")
def replay_run(file: str):
    path = (ROOT / file).resolve()
    if LOGS.resolve() not in path.parents or path.suffix != ".json" or not path.exists():
        raise HTTPException(404, "no such log")
    try:
        return replay(path)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, f"cannot replay: {e}") from e


def _session(sid: str) -> Session:
    if sid not in SESSIONS:
        raise HTTPException(404, "no such session; start a new one")
    return SESSIONS[sid]


def main() -> None:
    global LLM
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--provider", default="ollama")
    ap.add_argument("--model", default="qwen2.5:7b-8k")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    LLM = OpenAICompatibleLLM(provider=args.provider, model=args.model)
    if DIST.exists():
        app.mount("/", StaticFiles(directory=DIST, html=True), name="web")
    else:
        print("web/dist not found: build the frontend with `npm install && npm run build` in web/")
    print(f"I, Agent UI on http://localhost:{args.port}  ({LLM.provider}, {LLM.model})")
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
