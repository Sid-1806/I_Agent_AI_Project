"""Tier 2: the Procedural layer (LLM orchestrator).

Owner: Rudraksh

A hand-written ReAct loop: the LLM reasons, calls a tool, reads the result, and repeats until it
gives a final answer. Every step is recorded in a trace so each claim in the answer can be traced
back to the tool result it came from.

The LLM is reached through the OpenAI-compatible chat API, which Groq and Ollama both provide:
    IAGENT_PROVIDER = groq (default) | ollama
    IAGENT_MODEL    = model name (defaults below)
    GROQ_API_KEY    = your Groq key (in .env, never committed)
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional, Protocol

from .schemas import SELF
from .tools import ToolRegistry

PROMPT_PATH = Path(__file__).parent / "prompts" / "system.md"

PROVIDERS = {
    "groq": {"base_url": "https://api.groq.com/openai/v1", "key_env": "GROQ_API_KEY",
             "default_model": "openai/gpt-oss-20b"},
    "ollama": {"base_url": "http://localhost:11434/v1", "key_env": None,
               "default_model": "llama3.1:8b"},
}


class ToolCallFormatError(Exception):
    """The model produced a tool call the API could not parse."""


class LLM(Protocol):
    model: str

    def complete(self, messages: list[dict], tools: Optional[list[dict]]) -> dict:
        """Return {"content": str | None, "tool_calls": [{"id", "name", "arguments"}]}."""


class OpenAICompatibleLLM:
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None, temperature: float = 0.0):
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        import openai

        self.provider = provider or os.getenv("IAGENT_PROVIDER", "groq")
        cfg = PROVIDERS[self.provider]
        self.model = model or os.getenv("IAGENT_MODEL") or cfg["default_model"]
        key = os.getenv(cfg["key_env"]) if cfg["key_env"] else "ollama"
        if not key:
            raise RuntimeError(f"{cfg['key_env']} is not set. Put it in a .env file (see .env.example).")
        self.temperature = temperature
        self._openai = openai
        self.client = openai.OpenAI(base_url=cfg["base_url"], api_key=key, max_retries=4)

    def complete(self, messages: list[dict], tools: Optional[list[dict]]) -> dict:
        kwargs: dict[str, Any] = {"model": self.model, "messages": messages, "temperature": self.temperature}
        if tools:
            kwargs.update(tools=tools, tool_choice="auto")
        try:
            resp = self.client.chat.completions.create(**kwargs)
        except self._openai.BadRequestError as e:
            if "tool" in str(e).lower():
                raise ToolCallFormatError(str(e)) from e
            raise
        msg = resp.choices[0].message
        calls = [{"id": c.id, "name": c.function.name, "arguments": c.function.arguments or "{}"}
                 for c in (msg.tool_calls or [])]
        return {"content": msg.content, "tool_calls": calls}


@dataclass
class AgentResult:
    question: str
    answer: str
    trace: list[dict] = field(default_factory=list)
    belief_changes: list[str] = field(default_factory=list)

    @property
    def tools_called(self) -> list[str]:
        return [s["name"] for s in self.trace if s["type"] == "tool_call"]


class Agent:
    def __init__(self, tools: ToolRegistry, llm: LLM, system_prompt: Optional[str] = None,
                 max_steps: int = 12, max_format_retries: int = 2, self_check: bool = True,
                 max_self_checks: int = 4):
        self.tools = tools
        self.llm = llm
        self.system_prompt = system_prompt or PROMPT_PATH.read_text(encoding="utf-8")
        self.max_steps = max_steps
        self.max_format_retries = max_format_retries
        self.self_check = self_check
        self.max_self_checks = max_self_checks
        self.reset()

    def reset(self) -> None:
        self.messages: list[dict] = [{"role": "system", "content": self.system_prompt}]
        self.history: list[dict] = []      # trace steps of earlier turns in this conversation
        self.user_turns: list[str] = []

    def ask(self, question: str, on_step: Optional[Callable[[dict], None]] = None) -> AgentResult:
        """One user turn. Conversation history is kept between calls, so multi-turn scenarios work.

        on_step, if given, is called with each trace step as soon as it happens (used by the web UI).
        """
        store = self.tools.store
        v_before = store.snapshot(f"before: {question}")
        self.messages.append({"role": "user", "content": question})
        self.user_turns.append(question)
        self.tools.user_said.append(question)
        self.tools.open_conflicts.clear()
        self.tools.scanned.clear()
        trace = _Trace(on_step)
        answer = None
        format_errors = 0
        self_checks = 0
        failed: dict[tuple[str, str], int] = {}  # identical failing tool calls this turn

        for step in range(1, self.max_steps + 1):
            try:
                reply = self.llm.complete(self.messages, self.tools.schemas)
            except ToolCallFormatError as e:
                format_errors += 1
                trace.append({"step": step, "type": "error", "text": f"malformed tool call: {e}"[:300]})
                if format_errors > self.max_format_retries:
                    break
                self.messages.append({"role": "user", "content":
                                      "Your last tool call was rejected: " + _api_error_detail(e) +
                                      " Call the tool again with arguments that match its schema exactly."})
                continue

            if not reply["tool_calls"] and reply["content"]:
                # Small models sometimes write a tool call as text instead of calling it.
                calls, leftover = extract_text_tool_calls(reply["content"], self.tools.names,
                                                          self._required_params())
                if calls:
                    trace.append({"step": step, "type": "note", "text": f"parsed {len(calls)} tool call(s) from text"})
                    reply = {"content": leftover or None, "tool_calls": calls}

            if not reply["tool_calls"]:
                candidate = (reply["content"] or "").strip()
                self.messages.append({"role": "assistant", "content": candidate})
                problems = self.check_answer(candidate, trace) if self.self_check else []
                if problems and self_checks < self.max_self_checks:
                    self_checks += 1
                    trace.append({"step": step, "type": "draft", "text": candidate})
                    trace.append({"step": step, "type": "self_check", "text": " ".join(problems)})
                    self.messages.append({"role": "user", "content": "[Self-check] " + " ".join(problems) +
                                          f" Then answer the user's question: \"{question}\""})
                    continue
                answer = candidate
                trace.append({"step": step, "type": "answer", "text": answer})
                break

            if reply["content"]:
                trace.append({"step": step, "type": "thought", "text": reply["content"].strip()})
            self.messages.append({"role": "assistant", "content": reply["content"], "tool_calls": [
                {"id": c["id"], "type": "function", "function": {"name": c["name"], "arguments": c["arguments"]}}
                for c in reply["tool_calls"]]})
            for call in reply["tool_calls"]:
                result = self.tools.execute(call["name"], call["arguments"])
                key = (call["name"], json.dumps(_parse(call["arguments"]), sort_keys=True))
                if not json.loads(result).get("ok"):
                    failed[key] = failed.get(key, 0) + 1
                    if failed[key] >= 2:
                        r = json.loads(result)
                        r["error"] += (f" This exact call has now failed {failed[key]} times; repeating it will not "
                                       f"work. Do something else, or answer the user's question with what you know.")
                        result = json.dumps(r)
                trace.append({"step": step, "type": "tool_call", "name": call["name"],
                              "arguments": _parse(call["arguments"]), "result": json.loads(result)})
                self.messages.append({"role": "tool", "tool_call_id": call["id"], "content": result})

        if answer is None:
            # Out of steps: ask for a final answer with tools disabled.
            self.messages.append({"role": "user", "content": "Stop calling tools and give your final answer now."})
            try:
                answer = (self.llm.complete(self.messages, None)["content"] or "").strip()
            except ToolCallFormatError:
                answer = ""
            trace.append({"step": self.max_steps + 1, "type": "answer", "text": answer})
            self.messages.append({"role": "assistant", "content": answer})

        self.history.extend(trace)
        v_after = store.snapshot(f"after: {question}")
        return AgentResult(question=question, answer=answer, trace=list(trace),
                           belief_changes=store.diff(v_before, v_after))

    def _required_params(self) -> dict[str, set[str]]:
        return {t["function"]["name"]: set(t["function"]["parameters"].get("required", []))
                for t in self.tools.schemas}

    def check_answer(self, answer: str, trace: list[dict]) -> list[str]:
        """Epistemic validation: compare a draft answer with what actually happened in the layers.

        Returns a list of problems to send back to the LLM; empty means the answer is accepted.
        Evidence gathered in earlier turns of the same conversation counts.
        """
        trace = self.history + trace
        problems = []
        if not answer:
            problems.append("Your reply was empty. Call a tool if you need more information, "
                            "otherwise give your final answer.")
            return problems
        updated = any(s["type"] == "tool_call" and s["name"] == "update_belief" and s["result"].get("ok")
                      for s in trace)
        checked_memory = any(s["type"] == "tool_call" and s["name"] in _MEMORY_READS for s in trace)
        if not checked_memory:
            named = sorted({e for q in self.user_turns[-1:] for e in _ENTITY_ID.findall(q.lower())})
            call = f'query_beliefs(entity="{named[0]}")' if len(named) == 1 else "query_beliefs()"
            problems.append(f"You have not checked memory yet: no query_beliefs call appears in this conversation, "
                            f"and writing that you checked does not check it. Do not answer yet; make this tool "
                            f"call now: {call} (and get_pose if the question is about your route or location).")
        recorded_user = any(s["type"] == "tool_call" and s["name"] == "record_user_belief" and s["result"].get("ok")
                            for s in trace)
        stated = [q for q in self.user_turns if _USER_STATES.search(q)]
        if stated and not recorded_user:
            problems.append(f"The user told you what they believe (\"{stated[0]}\"), but you have not called the "
                            f"record_user_belief tool. Writing that you recorded it does not record it. Do not "
                            f"answer yet; make this tool call now: {_user_belief_call(stated[0])}")
        observed = _observed_entities(trace)
        unseen = sorted({e for e in _ENTITY_ID.findall(answer.lower()) if e not in observed})
        if unseen and not _SAYS_UNKNOWN.search(answer):
            problems.append(f"No memory record or sensor reading mentions {', '.join(unseen)}. The camera sees "
                            f"only the room you are in ({self.tools.env.robot['room']}), so an object it does not "
                            f"list is not in view. Do not give {'it' if len(unseen) == 1 else 'them'} properties "
                            f"seen on other objects; say plainly that you do not know.")
        for entity in self.tools.unverified_map_entities(answer, trace):
            problems.append(f"Your answer relies on the static map for {entity['subject']} "
                            f"({entity['predicate']} = {entity['value']}, {entity['age_s']} s old) without a live "
                            f"reading. {entity['how_to_check']} before answering.")
        downgrades = any(u["new_confidence"] < u["old_confidence"] for s in trace
                         if s["type"] == "tool_call" and s["result"].get("ok")
                         for u in (s["result"].get("data") or {}).get("confidence_updates", []))
        if _CLAIMS_DOWNGRADE.search(answer) and not downgrades:
            problems.append("You said a belief was downgraded, but no confidence in memory went down. Only the "
                            "static map's confidence changes, and only when a live sensor reading contradicts "
                            "it; other robots' reports and the user's beliefs are kept as they are. Do not "
                            "claim it.")
        this_turn = trace[len(self.history):]
        lowered = [u for s in this_turn if s["type"] == "tool_call" and s["result"].get("ok")
                   for u in (s["result"].get("data") or {}).get("confidence_updates", [])
                   if u["new_confidence"] < u["old_confidence"]]
        if lowered and not _says(answer, lowered[-1]["perspective"]):
            u = lowered[-1]
            problems.append(f"Your readings lowered the static {u['perspective']}'s confidence in {u['entity']}."
                            f"{u['property']} = {u['value']} to {u['new_confidence']}. Say in your answer that the "
                            f"{u['perspective']} said {u['value']} and that its confidence is now {u['new_confidence']}.")
        if _ASKS_PROVENANCE.search(self.user_turns[-1]) and not any(
                s["type"] == "tool_call" and s["name"] == "get_provenance" for s in this_turn):
            problems.append("The user is asking where, when, why or how a belief arose. Answer from the "
                            "provenance log, not from the conversation: call get_provenance for the entity "
                            "first and cite its source, reason and age.")
        if _ASKS_WHY.search(self.user_turns[-1]):
            reasons = {r["reason"] for s in this_turn if s["type"] == "tool_call" and s["name"] == "get_provenance"
                       and s["result"].get("ok") for r in (s["result"].get("data") or {}).get("history", [])
                       if r.get("reason") and r["reason"] != "initial load"}
            missing = [r for r in sorted(reasons) if not any(_says(answer, w) for w in _content_words(r))]
            if reasons and len(missing) == len(reasons):
                problems.append(f"The user asked why. The provenance log records the reason: "
                                f"{'; '.join(repr(r) for r in missing)}. Include that reason in your answer.")
        for s in this_turn:
            if s["type"] == "tool_call" and s["name"] == "record_user_belief" and s["result"].get("ok"):
                w = (s["result"].get("data") or {}).get("written") or {}
                if w and not _says(answer, w["value"]):
                    problems.append(f"You recorded the user's belief that {w['entity']}.{w['property']} = "
                                    f"{w['value']}, but your answer does not mention it. Tell the user what you "
                                    f"recorded as their view, separately from what you observed yourself.")
        evidence = " ".join(self.user_turns) + " " + " ".join(
            json.dumps(s["result"]) for s in trace if s["type"] == "tool_call")
        invented = [c for c in _COLOURS if _says(answer, c) and not _says(evidence, c)]
        if invented:
            problems.append(f"No tool result or user message mentions {', '.join(invented)}. Every value in your "
                            f"answer must come from a tool result in this conversation or from the user; remove "
                            f"{'it' if len(invented) == 1 else 'them'}, or say that you do not know.")
        planned = self.tools.store.get("robot", "planned_route", SELF)
        facing = {r: d for d, r in self.tools.env.robot["facing"].items()}
        if (planned and _ASKS_OWN_ROUTE.search(self.user_turns[-1]) and planned.obj in facing
                and planned.obj not in self.tools.scanned):
            problems.append(f"Memory says your planned route is {planned.obj}, which lies {facing[planned.obj]} of "
                            f"you. Scan that route before answering: read_lidar(direction=\"{facing[planned.obj]}\").")
        if _VAGUE_ROBOT.search(answer):
            unnamed = sorted({(persp, e, p) for e, p, persp in self.tools.shown
                              if persp.startswith("agent:") and _says(answer, e) and not _says(answer, persp[6:])})
            if unnamed:
                now = self.tools.store.clock.now()
                listing = "; ".join(f"{persp[6:]} reported {e}.{p} = {b.obj} {round((now - b.timestamp) / 60)} min ago"
                                    for persp, e, p in unnamed if (b := self.tools.store.get(e, p, persp)))
                problems.append(f"Name the robot instead of writing 'another robot': {listing}. Say which robot "
                                f"reported it and how long ago.")
        if _YES_NO_QUESTION.match(self.user_turns[-1].strip()) and not _YES_NO_ANSWER.search(answer[:80]):
            problems.append("The user asked a yes/no question. Start your answer with \"Yes\" or \"No\", "
                            "then give the evidence.")
        used = {s["name"] for s in trace if s["type"] == "tool_call" and s["result"].get("ok")}
        for m in _CLAIMS_SENSOR.finditer(answer):
            tool = "read_camera" if m.group(1).lower() == "camera" else "read_lidar"
            if tool not in used:
                problems.append(f"You wrote that the {m.group(1)} showed something, but you never called {tool}. "
                                f"Call it now, or do not claim it.")
                break
        if _ANNOUNCES_ACTION.search(answer):
            problems.append("You described actions you are going to take but did not take them. Call the "
                            "tools now, then answer from their results.")
        claim = _CLAIMS_UPDATE.search(answer)
        if claim and not updated and not (recorded_user and "record" in claim.group(0).lower()):
            problems.append("You said you updated a belief, but you never called update_belief, "
                            "so memory is unchanged. Call update_belief now, or do not claim it.")
        if checked_memory:
            store = self.tools.store
            for entity in store.subjects():
                if entity == "robot" or not _says(answer, entity):
                    continue
                hidden = sorted({f"{b.predicate} from {b.perspective}" for b in store.query(entity)
                                 if (entity, b.predicate, b.perspective) not in self.tools.shown})
                if hidden:
                    problems.append(f"Memory holds records about {entity} that you have not looked at "
                                    f"({', '.join(hidden)}). Call query_beliefs(entity=\"{entity}\") and take "
                                    f"every record into account before answering.")
        store = self.tools.store
        named = {e for e in store.subjects() if e != "robot" and _says(answer, e)}
        groups = {(d["entity"], d["property"]): d for e in named
                  for d in self.tools._disagreements([self.tools._with_age(b) for b in store.query(e)])}
        for (entity, prop), d in {**self.tools.shown_disagreements, **groups}.items():
            records = [r for r in d["newest_first"] if r["perspective"] != SELF]
            if len({r["value"] for r in records}) < 2:
                continue
            if not (_says(answer, entity) or any(_says(answer, r["value"]) for r in records)):
                continue
            missing = [r for r in records if not _says(answer, r["value"])]
            if missing:
                listing = "; ".join(f"{r['value']} from {r['source']} ({r['recorded']})" for r in records)
                problems.append(f"Your records disagree about {entity}.{prop}: {listing}. Your answer leaves out "
                                f"{', '.join(r['value'] + ' from ' + r['source'] for r in missing)}. Report every "
                                f"record with its source and age, then say which one you trust more and why.")
        for c in self.tools.actionable_conflicts():
            stored = ", ".join(f"{x['perspective']} says {x['stored_value']}" for x in c["conflicts"])
            if c["confirmed"]:
                problems.append(f"Unresolved conflict: {c['sensor']} observed {c['subject']}.{c['predicate']} = "
                                f"{c['observed']}, but memory has {stored}. Do not answer yet. Your next reply must "
                                f"be this tool call: update_belief(entity=\"{c['subject']}\", "
                                f"property=\"{c['predicate']}\", value=\"{c['observed']}\", "
                                f"source=\"{c['sensor']}\", confidence=1.0, reason=\"live {c['sensor']} reading\")")
            else:
                problems.append(f"Unconfirmed conflict: one {c['sensor']} reading gave {c['subject']}."
                                f"{c['predicate']} = {c['observed']}, but memory has {stored}. Read the sensor "
                                f"again; if it agrees, call update_belief, otherwise trust the readings that agree.")
        conflicts = [p for p in problems if p.startswith(("Unresolved conflict", "Unconfirmed conflict"))]
        return conflicts + [p for p in problems if p not in conflicts]


class _Trace(list):
    """The trace of one turn; also reports each step to an optional listener."""

    def __init__(self, on_step: Optional[Callable[[dict], None]] = None):
        super().__init__()
        self.on_step = on_step

    def append(self, step: dict) -> None:
        super().append(step)
        if self.on_step:
            self.on_step(step)


_MEMORY_READS = {"query_beliefs"}  # current beliefs; get_provenance is the history behind them
_COLOURS = ("red", "blue", "green", "brown", "yellow", "orange", "black", "white", "purple", "grey", "gray",
            "pink", "olive", "beige")


def _says(text: str, term: str) -> bool:
    """Whether the text names a term, treating '_' and ' ' alike ('box_01' matches 'box 01')."""
    norm = lambda x: re.sub(r"[_\s]+", " ", x.lower())
    return re.search(r"(?<![a-z0-9])" + re.escape(norm(term)) + r"(?![a-z0-9])", norm(text)) is not None
_USER_STATES = re.compile(r"\bI (left|put|placed|dropped|moved|think|believe|thought|saw|remember|"
                          r"painted|parked|stored)\b[^.?!]{0,60}", re.IGNORECASE)
_ENTITY_ID = re.compile(r"\b[a-z]+_\d+\b")
_SAYS_UNKNOWN = re.compile(r"\b(don't know|do not know|no (memory )?records?|no information|unknown|not (able|found)|"
                           r"unable|cannot (determine|provide)|can't (determine|provide)|no data|don't have|"
                           r"do not have|no (sensor )?readings?)\b", re.IGNORECASE)
_CLAIMS_UPDATE = re.compile(r"\b(i\s+(have\s+)?updated|i've updated|updated my (belief|memory)|"
                            r"i\s+(have\s+)?(recorded|downgraded))", re.IGNORECASE)
_CLAIMS_DOWNGRADE = re.compile(r"\b(downgraded|lowered (its|their|the) confidence|reduced (its|their|the) "
                               r"confidence)\b", re.IGNORECASE)
_CLAIMS_SENSOR = re.compile(r"\b(camera|lidar)\b[^.]{0,40}?\b(confirm|show|detect|see|saw|sees|report|indicat|observ|perceiv)",
                            re.IGNORECASE)
_YES_NO_QUESTION = re.compile(r"(can|is|are|do|does|did|has|have|will)\b", re.IGNORECASE)
_YES_NO_ANSWER = re.compile(r"\b(yes|no)\b", re.IGNORECASE)
_ASKS_WHY = re.compile(r"\bwhy\b", re.IGNORECASE)
_STOPWORDS = {"the", "and", "from", "with", "that", "this", "item", "logged", "action", "reported", "robot",
              "during", "because", "after", "before", "into", "onto", "were", "was", "has", "have"}


def _content_words(text: str) -> list[str]:
    """Words of a logged reason that say something (not ids, numbers or filler)."""
    return [w for w in re.findall(r"[a-z]+", text.lower()) if len(w) > 3 and w not in _STOPWORDS
            and not re.fullmatch(r"(bot|room|route|box|crate|cup)", w)]


def _user_belief_call(statement: str) -> str:
    """The record_user_belief call for a user statement such as "I left box_01 in Room 101"."""
    entity = (_ENTITY_ID.findall(statement.lower()) or ["<entity>"])[0]
    room = re.search(r"\broom[ _]?(\d+)", statement, re.IGNORECASE)
    colour = next((c for c in _COLOURS if re.search(rf"\b{c}\b", statement, re.IGNORECASE)), None)
    if room:
        prop, value = "located_at", f"Room_{room.group(1)}"
    elif colour:
        prop, value = "color", colour
    else:
        prop, value = "<property>", "<value>"
    evidence = statement.replace('"', "'")
    return (f'record_user_belief(entity="{entity}", property="{prop}", value="{value}", '
            f'evidence="{evidence}")')


_ASKS_OWN_ROUTE = re.compile(r"\b(your|my) (planned )?(route|path)\b|\bdrive your\b", re.IGNORECASE)
_VAGUE_ROBOT = re.compile(r"\b(another|other|a second|second|secondary|maintenance|an?) (robot|bot|agent)s?\b",
                          re.IGNORECASE)
_ASKS_PROVENANCE = re.compile(r"\b(why|where did you (learn|get|hear)|who (told|reported|said)|when (was|did)|"
                              r"what caused|how do you know|history)\b", re.IGNORECASE)
_ANNOUNCES_ACTION = re.compile(r"\b(i will|i'll|let me|i am going to|i'm going to|i need to|i will need to)\s+(now\s+|first\s+|need to\s+)?"
                               r"(check|verify|read|use|query|look|scan|update|record|confirm|inspect|call|do that|drive|move|go)\b",
                               re.IGNORECASE)


def run_baseline(llm: LLM, memory: list[dict], question_turns: list[str]) -> AgentResult:
    """Baseline for evaluation: the same LLM, memory pasted in as plain text, and no tools.

    It cannot read sensors or update memory, so it shows what the three-layer design adds.
    """
    facts = "\n".join(f"- {m['subject']}.{m['predicate']} = {m['obj']} (perspective {m['perspective']}, "
                      f"source {m['source']}, confidence {m['confidence']})" for m in memory)
    messages = [{"role": "system", "content":
                 "You are the reasoning module of a mobile robot. Your stored knowledge:\n" + facts +
                 "\nAnswer the user's questions in 2 to 5 sentences."}]
    answer = ""
    for q in question_turns:
        messages.append({"role": "user", "content": q})
        answer = (llm.complete(messages, None)["content"] or "").strip()
        messages.append({"role": "assistant", "content": answer})
    return AgentResult(question=question_turns[-1], answer=answer,
                       trace=[{"step": 1, "type": "answer", "text": answer}])


def extract_text_tool_calls(text: str, tool_names: list[str],
                            required: Optional[dict[str, set[str]]] = None) -> tuple[list[dict], str]:
    """Find tool calls written as text instead of made through the API.

    Three forms are recognised:
      update_belief {"entity": ...}                          a tool name directly followed by JSON
      {"name": "move", "arguments": {"route": "route_B"}}    a JSON call object, e.g. in a ```json block
      {"entity": ..., "property": ..., "value": ..., ...}    bare arguments that fit exactly one tool
    Returns (calls, remaining_text).
    """
    decoder = json.JSONDecoder()
    required = required or {}
    calls, spans = [], []

    def add(name: str, args: dict, start: int, end: int) -> None:
        calls.append({"id": f"text_call_{len(calls)}", "name": name, "arguments": json.dumps(args)})
        spans.append((start, end))

    named = re.compile(r"\b(" + "|".join(map(re.escape, tool_names)) + r")\b\s*(\(\s*)?(?=\{)")
    pos = 0
    while (m := named.search(text, pos)):
        try:
            args, end = decoder.raw_decode(text, m.end())
        except json.JSONDecodeError:
            pos = m.end()
            continue
        if isinstance(args, dict):
            add(m.group(1), args, m.start(), end)
        pos = end

    # query_beliefs(entity="box_01", property="color") or get_pose()
    pycall = re.compile(r"\b(" + "|".join(map(re.escape, tool_names)) +
                        r")\(\s*((?:\w+\s*=\s*(?:\"[^\"]*\"|'[^']*'|[\w.]+)\s*,?\s*)*)\)")
    for m in pycall.finditer(text):
        if any(a <= m.start() < b for a, b in spans):
            continue
        args = {k: (v1 or v2 or v3) for k, v1, v2, v3 in
                re.findall(r"(\w+)\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([\w.]+))", m.group(2))}
        add(m.group(1), args, m.start(), m.end())

    pos = 0
    while (i := text.find("{", pos)) != -1:
        if any(a <= i < b for a, b in spans):
            pos = i + 1
            continue
        try:
            obj, end = decoder.raw_decode(text, i)
        except json.JSONDecodeError:
            pos = i + 1
            continue
        pos = end
        if not isinstance(obj, dict):
            continue
        args = obj.get("arguments", obj.get("parameters"))
        if obj.get("name") in tool_names and isinstance(args, (dict, type(None))):
            add(obj["name"], args or {}, i, end)
            continue
        fits = [n for n in tool_names if required.get(n) and required[n] <= set(obj)]
        if len(fits) == 1:
            add(fits[0], obj, i, end)

    spans.sort()
    leftover, last = [], 0
    for a, b in spans:
        leftover.append(text[last:a])
        last = b
    leftover.append(text[last:])
    rest = re.sub(r"```(json)?\s*```", "", "".join(leftover))
    return calls, re.sub(r"\s*-\s*$", "", rest).strip()


_NON_EVIDENCE_KEYS = ("note", "advice", "error", "ignored_arguments")


def _observed_entities(trace: list[dict]) -> set[str]:
    """Entity ids that appear in data a tool returned.

    Explanatory fields such as "No provenance records for 'crate_07'" are skipped: a tool saying it
    knows nothing about something is not evidence about it.
    """
    found: set[str] = set()

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k not in _NON_EVIDENCE_KEYS:
                    walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        elif isinstance(x, str):
            found.update(_ENTITY_ID.findall(x.lower()))
    for step in trace:
        if step["type"] == "tool_call" and step["result"].get("ok"):
            walk(step["result"].get("data"))
    return found


def _api_error_detail(e: Exception) -> str:
    text = str(e)
    for marker in ("'message': '", '"message": "'):
        if marker in text:
            return text.split(marker, 1)[1].split(marker[-1], 1)[0][:300]
    return text[:300]


def _parse(arguments: str) -> Any:
    try:
        return json.loads(arguments or "{}")
    except json.JSONDecodeError:
        return arguments
