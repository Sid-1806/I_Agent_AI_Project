"""Run one scenario and print the full ReAct trace. This is the mid-sem demo.

    python run_scenario.py --list
    python run_scenario.py A1                  # Scenario A: map says clear, LiDAR says blocked
    python run_scenario.py B1                  # Scenario B: red / brown / blue
    python run_scenario.py A1 --chat           # then keep asking your own questions
    python run_scenario.py A1 --model openai/gpt-oss-120b

Owner: Udit
"""
from __future__ import annotations

import argparse
import json
import sys

from i_agent.evaluation import run_checks
from i_agent.procedural import Agent, AgentResult, OpenAICompatibleLLM
from i_agent.scenario import all_scenarios, build_world, load_scenario

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DIM, BOLD, CYAN, YELLOW, GREEN, RED, BLUE, RESET = (
    "\033[2m", "\033[1m", "\033[36m", "\033[33m", "\033[32m", "\033[31m", "\033[34m", "\033[0m")


def short(value, limit=220) -> str:
    text = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
    return text if len(text) <= limit else text[:limit] + " ..."


def print_turn(result: AgentResult) -> None:
    print(f"\n{BOLD}USER:{RESET} {result.question}")
    for s in result.trace:
        if s["type"] == "thought":
            print(f"  {DIM}thought:{RESET} {s['text']}")
        elif s["type"] == "tool_call":
            print(f"  {CYAN}→ {s['name']}({short(s['arguments'], 160)}){RESET}")
            print(f"    {DIM}{short(s['result'])}{RESET}")
        elif s["type"] == "draft":
            print(f"  {DIM}draft answer:{RESET} {DIM}{s['text']}{RESET}")
        elif s["type"] == "self_check":
            print(f"  {YELLOW}self-check:{RESET} {s['text']}")
        elif s["type"] == "error":
            print(f"  {RED}! {s['text']}{RESET}")
        elif s["type"] == "answer":
            print(f"\n{BOLD}{GREEN}AGENT:{RESET} {s['text']}")
    if result.belief_changes:
        print(f"\n{YELLOW}Belief graph changes this turn:{RESET}")
        for line in result.belief_changes:
            print(f"  {line}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenario", nargs="?", help="scenario id or prefix, e.g. A1 or B1_three_colors")
    ap.add_argument("--list", action="store_true", help="list the scenarios")
    ap.add_argument("--chat", action="store_true", help="after the scripted turns, keep asking questions")
    ap.add_argument("--provider", help="groq (default) or ollama")
    ap.add_argument("--model", help="model name, e.g. llama-3.1-8b-instant")
    args = ap.parse_args()

    if args.list or not args.scenario:
        for s in all_scenarios():
            print(f"{s['id']:<24} [{s.get('type')}] {s.get('description', '')}")
        return

    scenario = load_scenario(args.scenario)
    world = build_world(scenario)
    llm = OpenAICompatibleLLM(provider=args.provider, model=args.model)
    agent = Agent(world.tools, llm)

    print(f"{BOLD}{scenario['id']}{RESET}  ({llm.model})\n{scenario.get('description', '')}")
    print(f"\n{BLUE}Belief graph at start:{RESET}\n{world.store.describe()}")

    results = []
    for question in scenario["turns"]:
        results.append(agent.ask(question))
        print_turn(results[-1])

    checks = run_checks(scenario.get("expect", {}), results, world.store, scenario["turns"])
    print(f"\n{BLUE}Belief graph at end:{RESET}\n{world.store.describe()}")
    print(f"\n{BLUE}Checks:{RESET}")
    for c in checks:
        mark = f"{GREEN}PASS{RESET}" if c.passed else f"{RED}FAIL{RESET}"
        print(f"  {mark} [{c.kind}] {c.name} {DIM}{c.detail}{RESET}")
    print(f"\n{'PASSED' if all(c.passed for c in checks) else 'FAILED'}: "
          f"{sum(c.passed for c in checks)}/{len(checks)} checks")

    if args.chat:
        print(f"\n{DIM}Chat mode: ask anything, empty line to quit.{RESET}")
        while True:
            try:
                q = input(f"\n{BOLD}you> {RESET}").strip()
            except EOFError:
                break
            if not q:
                break
            print_turn(agent.ask(q))


if __name__ == "__main__":
    main()
