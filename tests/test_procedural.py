"""Tests for the tool registry and the ReAct loop, using a scripted fake LLM (no API calls).

Owner: Rudraksh
"""
import json

from i_agent.evaluation import run_checks
from i_agent.procedural import Agent, ToolCallFormatError, extract_text_tool_calls
from i_agent.scenario import build_world, load_scenario


class ScriptedLLM:
    """Replays a fixed list of replies: each is a list of (tool, args) calls or a final answer string."""

    model = "scripted"

    def __init__(self, replies):
        self.replies = list(replies)
        self.seen_messages = []

    def complete(self, messages, tools):
        self.seen_messages.append(list(messages))
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        if isinstance(reply, str):
            return {"content": reply, "tool_calls": []}
        return {"content": None, "tool_calls": [
            {"id": f"call_{i}", "name": name, "arguments": json.dumps(args)} for i, (name, args) in enumerate(reply)]}


IDEAL_A1 = [
    [("query_beliefs", {"subject": "route_A"})],
    [("read_lidar", {"direction": "front"})],
    [("update_belief", {"subject": "route_A", "predicate": "status", "value": "blocked", "source": "lidar_front",
                        "confidence": 0.95, "reason": "LiDAR shows obstacle at 12 cm"})],
    "No. My static map says route_A is clear, but my live LiDAR shows an obstacle 12 cm ahead, so it is "
    "blocked. I downgraded the map's confidence and updated my belief graph.",
]


def test_react_loop_runs_tools_and_passes_scenario_a_checks():
    scenario = load_scenario("A1")
    world = build_world(scenario)
    agent = Agent(world.tools, ScriptedLLM(IDEAL_A1))
    result = agent.ask(scenario["turns"][0])
    assert result.tools_called == ["query_beliefs", "read_lidar", "update_belief"]
    assert result.answer.startswith("No.")
    assert any("route_A.status [self] = blocked" in line for line in result.belief_changes)
    checks = run_checks(scenario["expect"], [result], world.store, scenario["turns"])
    assert all(c.passed for c in checks), [c for c in checks if not c.passed]


def test_checks_catch_a_lazy_agent():
    scenario = load_scenario("A1")
    world = build_world(scenario)
    agent = Agent(world.tools, ScriptedLLM(["Yes, the route is clear according to my map."]), self_check=False)
    result = agent.ask(scenario["turns"][0])
    checks = run_checks(scenario["expect"], [result], world.store, scenario["turns"])
    failed = {c.kind for c in checks if not c.passed}
    assert {"tools", "memory", "answer"} <= failed


def test_grounding_check_flags_invented_colour():
    scenario = load_scenario("H1")
    world = build_world(scenario)
    agent = Agent(world.tools, ScriptedLLM([[("query_beliefs", {"subject": "crate_07"})],
                                            "crate_07 is red."]), self_check=False)
    result = agent.ask(scenario["turns"][0])
    checks = run_checks(scenario["expect"], [result], world.store, scenario["turns"])
    grounding = [c for c in checks if c.kind == "grounding"][0]
    assert not grounding.passed and "red" in grounding.detail


def test_bad_tool_calls_are_reported_not_raised():
    world = build_world(load_scenario("A1"))
    out = json.loads(world.tools.execute("no_such_tool", "{}"))
    assert out["ok"] is False and "unknown tool" in out["error"]
    out = json.loads(world.tools.execute("read_lidar", "{not json"))
    assert out["ok"] is False
    out = json.loads(world.tools.execute("update_belief", {"entity": "x"}))
    assert out["ok"] is False and "bad arguments" in out["error"]


def test_malformed_call_is_retried():
    world = build_world(load_scenario("A1"))
    llm = ScriptedLLM([ToolCallFormatError("tool_use_failed"), "Done."])
    result = Agent(world.tools, llm, self_check=False).ask("hello")
    assert result.answer == "Done."
    assert result.trace[0]["type"] == "error"


def test_step_limit_forces_final_answer():
    world = build_world(load_scenario("A1"))
    llm = ScriptedLLM([[("get_pose", {})]] * 3 + ["Final answer."])
    result = Agent(world.tools, llm, max_steps=3).ask("where are you?")
    assert result.answer == "Final answer."


def test_conversation_history_is_kept_between_turns():
    world = build_world(load_scenario("B1"))
    llm = ScriptedLLM(["ok", "second"])
    agent = Agent(world.tools, llm, self_check=False)
    agent.ask("first question")
    agent.ask("second question")
    contents = [m.get("content") for m in llm.seen_messages[-1]]
    assert "first question" in contents and "second question" in contents


def test_sensor_readings_are_cross_checked_against_memory():
    world = build_world(load_scenario("A3"))  # scripted LiDAR: 9 cm spike, then 240 cm
    first = json.loads(world.tools.execute("read_lidar", {"direction": "front"}))["data"]
    assert first["memory_check"]["conflicts"][0]["perspective"] == "map"
    assert "read once more" in first["memory_check"]["advice"]
    second = json.loads(world.tools.execute("read_lidar", {"direction": "front"}))["data"]
    assert second["memory_check"]["conflicts"] == []
    assert world.tools.actionable_conflicts() == []


def test_camera_flags_missing_object_and_lighting():
    world = build_world(load_scenario("A4"))
    data = json.loads(world.tools.execute("read_camera", {}))["data"]
    assert data["memory_check"]["conflicts"][0]["subject"] == "box_01"
    assert world.tools.actionable_conflicts()[0]["predicate"] == "located_at"

    world = build_world(load_scenario("B1"))
    data = json.loads(world.tools.execute("read_camera", {}))["data"]
    assert "yellow" in data["memory_check"]["conflicts"][0]["note"]
    assert world.tools.actionable_conflicts() == []  # other robots' records are not overwritten


def test_self_check_catches_claimed_but_missing_update():
    world = build_world(load_scenario("A5"))
    llm = ScriptedLLM([
        [("query_beliefs", {"subject": "route_A"}), ("read_lidar", {"direction": "front"})],
        "No. The route is blocked, so I updated my belief.",          # claims an update it never made
        [("update_belief", {"subject": "route_A", "predicate": "status", "value": "blocked",
                            "source": "lidar_front", "confidence": 0.95, "reason": "LiDAR 20 cm"})],
        "No. LiDAR shows route_A blocked at 20 cm; I updated my belief.",
    ])
    result = Agent(world.tools, llm).ask("Can you drive your planned route right now?")
    kinds = [s["type"] for s in result.trace]
    assert "self_check" in kinds and result.tools_called[-1] == "update_belief"
    assert world.store.get("route_A", "status", "self").obj == "blocked"


def test_self_check_can_be_disabled_for_ablation():
    world = build_world(load_scenario("A5"))
    llm = ScriptedLLM([[("read_lidar", {"direction": "front"})], "Blocked, I updated my belief."])
    result = Agent(world.tools, llm, self_check=False).ask("Can you drive your planned route right now?")
    assert result.answer == "Blocked, I updated my belief."
    assert world.store.get("route_A", "status", "self").obj == "clear"


def test_self_check_catches_announced_but_untaken_action():
    world = build_world(load_scenario("H1"))  # map and LiDAR agree that route_A is clear
    llm = ScriptedLLM([
        "To be sure, I will verify using my sensors.",
        [("query_beliefs", {"subject": "route_A"}), ("read_lidar", {"direction": "front"})],
        "Yes, route_A is clear according to my LiDAR.",
    ])
    result = Agent(world.tools, llm).ask("Is route_A clear?")
    assert any(s["type"] == "self_check" for s in result.trace)
    assert result.tools_called == ["query_beliefs", "read_lidar"]


def test_argument_aliases_are_mapped():
    world = build_world(load_scenario("A4"))
    out = json.loads(world.tools.execute("update_belief", {
        "object": "box_01", "predicate": "located_at", "value": "not_in_Room_101",
        "source": "camera", "confidence": 0.9, "reason": "not seen"}))
    assert out["ok"], out
    assert world.store.get("box_01", "located_at", "self").obj == "not_in_Room_101"
    out = json.loads(world.tools.execute("query_beliefs", {"subject": "box_01", "object": "Room_101"}))
    assert out["ok"] and out["data"]["ignored_arguments"] == ["object"]


def test_tool_calls_written_as_text_are_parsed():
    from i_agent.procedural import extract_text_tool_calls
    text = ('I will record it. -record_user_belief {"subject": "box_01", "predicate": "color", '
            '"value": "red", "evidence": "find the red box"} Then look around.')
    calls, rest = extract_text_tool_calls(text, ["record_user_belief", "read_camera"])
    assert calls[0]["name"] == "record_user_belief" and json.loads(calls[0]["arguments"])["value"] == "red"
    assert "record_user_belief" not in rest and rest.startswith("I will record it.")
    assert extract_text_tool_calls("Call read_camera to look.", ["read_camera"])[0] == []


def test_agent_executes_text_tool_calls():
    world = build_world(load_scenario("B1"))
    llm = ScriptedLLM(['-record_user_belief {"subject": "box_01", "predicate": "color", "value": "red", '
                       '"evidence": "red box"}', "Noted: you are looking for a red box."])
    result = Agent(world.tools, llm, self_check=False).ask("Please find the red box for me. It is box_01.")
    assert result.tools_called == ["record_user_belief"]
    assert world.store.get("box_01", "color", "user").obj == "red"


def test_self_check_requires_consulting_memory():
    world = build_world(load_scenario("A2"))
    llm = ScriptedLLM([
        [("read_lidar", {"direction": "right"})],
        "The right path is blocked.",
        [("query_beliefs", {"subject": "robot"}), ("get_pose", {})],
        "I face route_B at the front; I will scan it next.",
    ])
    result = Agent(world.tools, llm, max_self_checks=1).ask("Can you take your planned route right now?")
    assert "not checked memory" in [s for s in result.trace if s["type"] == "self_check"][0]["text"]
    lidar = result.trace[0]["result"]["data"]["payload"]
    assert lidar["status"] == "no_route" and lidar["routes_by_direction"] == {"front": "route_B"}


def test_predicate_used_as_subject_is_rejected():
    world = build_world(load_scenario("A4"))
    out = json.loads(world.tools.execute("update_belief", {
        "subject": "located_at", "predicate": "in_room", "value": "not visible",
        "source": "camera", "confidence": 0.9, "reason": "x"}))
    assert out["ok"] is False and "not an entity" in out["error"]


def test_query_beliefs_forgives_swapped_or_unknown_names():
    world = build_world(load_scenario("B2"))
    swapped = json.loads(world.tools.execute("query_beliefs", {"subject": "located_at", "predicate": "room"}))
    assert swapped["data"]["beliefs"][0]["value"] == "Room_205"
    unknown_pred = json.loads(world.tools.execute("query_beliefs", {"subject": "box_01", "predicate": "room"}))
    assert unknown_pred["data"]["beliefs"][0]["value"] == "Room_205"


def test_self_check_flags_properties_given_to_unobserved_entities():
    world = build_world(load_scenario("H1"))
    llm = ScriptedLLM([
        [("query_beliefs", {"subject": "crate_07"}), ("read_camera", {})],
        "The camera shows crate_07 is blue.",                   # blue belongs to box_01
        "I have no record of crate_07, so I don't know its colour.",
    ])
    result = Agent(world.tools, llm).ask("What color is crate_07 in Room 303?")
    check = [s for s in result.trace if s["type"] == "self_check"][0]["text"]
    assert "crate_07" in check and "don't know" in result.answer


def test_self_check_flags_answers_resting_on_an_unverified_map():
    world = build_world(load_scenario("A2"))  # map: route_B blocked; reality: clear
    llm = ScriptedLLM([
        [("query_beliefs", {})],
        "No, the map says route_B is blocked.",
        [("read_lidar", {"direction": "front"}), ("read_lidar", {"direction": "front"})],
        [("update_belief", {"subject": "route_B", "predicate": "status", "value": "clear",
                            "source": "lidar_front", "confidence": 0.95, "reason": "two clear scans"})],
        "Yes. The map says route_B is blocked, but two LiDAR scans show it clear, so I updated my belief.",
    ])
    result = Agent(world.tools, llm).ask("Can you take your planned route right now?")
    check = [s for s in result.trace if s["type"] == "self_check"][0]["text"]
    assert 'read_lidar(direction="front")' in check
    assert world.store.get("route_B", "status", "self").obj == "clear"


def test_entity_resolution_prefers_a_known_entity():
    world = build_world(load_scenario("A4"))
    out = json.loads(world.tools.execute("update_belief", {
        "object": "box_01", "subject": "located_at", "predicate": "located_at",
        "value": "not_in_Room_101", "source": "camera", "confidence": 0.9, "reason": "not seen"}))
    assert out["ok"], out
    assert world.store.get("box_01", "located_at", "self").obj == "not_in_Room_101"


def test_listing_a_route_is_not_the_same_as_scanning_it():
    world = build_world(load_scenario("A2"))
    llm = ScriptedLLM([
        [("query_beliefs", {}), ("read_lidar", {"direction": "right"})],   # lists route_B, measures nothing
        "No, the map says route_B is blocked.",
        [("read_lidar", {"direction": "front"}), ("read_lidar", {"direction": "front"})],
        [("update_belief", {"entity": "route_B", "property": "status", "value": "clear",
                            "source": "lidar_front", "confidence": 0.95, "reason": "two clear scans"})],
        "Yes, two LiDAR scans show route_B clear; the map was outdated and I updated my belief.",
    ])
    result = Agent(world.tools, llm).ask("Can you take your planned route right now?")
    assert any("static map for route_B" in s["text"] for s in result.trace if s["type"] == "self_check")


def test_evidence_from_earlier_turns_counts_and_user_beliefs_are_required():
    world = build_world(load_scenario("B2"))
    llm = ScriptedLLM([
        [("query_beliefs", {"entity": "box_01"}), ("read_camera", {})],
        "box_01 is not here; bot_02 logged it in Room_205.",
        [("record_user_belief", {"entity": "box_01", "property": "located_at", "value": "Room_101",
                                 "evidence": "I left box_01 in Room 101"})],
        "box_01 is not here; bot_02 logged it in Room_205.",
        "You think box_01 is in Room 101; my records say Room_205.",   # turn 2: no new tools needed
    ])
    agent = Agent(world.tools, llm)
    first = agent.ask("I left box_01 in Room 101 before lunch. Can you check whether it is still there?")
    assert "record_user_belief tool" in [s for s in first.trace if s["type"] == "self_check"][0]["text"]
    second = agent.ask("Where do I think box_01 is, and where is it actually?")
    assert not any(s["type"] == "self_check" for s in second.trace)
    assert "Room_205" in second.answer


def test_invented_values_cannot_be_written_to_memory():
    world = build_world(load_scenario("B3"))  # records say blue (bot_02) and green (bot_03)
    write = {"entity": "box_01", "property": "color", "source": "static_map", "confidence": 0.9, "reason": "x"}
    out = json.loads(world.tools.execute("update_belief", {**write, "value": "red"}))
    assert out["ok"] is False and "does not appear" in out["error"]
    world.tools.execute("query_beliefs", {"entity": "box_01"})
    out = json.loads(world.tools.execute("update_belief", {**write, "value": "green", "source": "camera"}))
    assert out["ok"] is True


def test_another_robots_report_cannot_be_copied_into_self():
    world = build_world(load_scenario("B3"))
    world.tools.execute("query_beliefs", {"entity": "box_01"})
    out = json.loads(world.tools.execute("update_belief", {
        "entity": "box_01", "property": "color", "value": "green", "source": "bot_03_log",
        "confidence": 0.85, "reason": "newest report"}))
    assert out["ok"] is False and "not one of your sensors" in out["error"]
    assert world.store.get("box_01", "color", "self") is None


def test_values_seen_on_one_object_cannot_be_written_to_another():
    world = build_world(load_scenario("H1"))  # camera sees box_01 (blue); crate_07 is unknown
    world.tools.execute("read_camera", {})
    out = json.loads(world.tools.execute("update_belief", {
        "entity": "crate_07", "property": "color", "value": "blue", "source": "camera",
        "confidence": 0.9, "reason": "x"}))
    assert out["ok"] is False and "crate_07" in out["error"]


def test_json_tool_calls_without_a_tool_name_are_parsed():
    names = ["update_belief", "move", "query_beliefs"]
    required = {"update_belief": {"entity", "property", "value", "source", "confidence", "reason"},
                "move": {"route"}, "query_beliefs": set()}
    text = ('I will record it.\n```json\n{"entity": "route_B", "property": "status", "value": "clear", '
            '"source": "lidar_front", "confidence": 1.0, "reason": "two readings"}\n```\n'
            'Then:\n```json\n{"name": "move", "arguments": {"route": "route_B"}}\n```')
    calls, rest = extract_text_tool_calls(text, names, required)
    assert [c["name"] for c in calls] == ["update_belief", "move"]
    assert json.loads(calls[1]["arguments"]) == {"route": "route_B"}
    assert "```" not in rest and "route_B" not in rest


def test_self_check_requires_every_disagreeing_record():
    world = build_world(load_scenario("B3"))
    llm = ScriptedLLM([
        [("query_beliefs", {"entity": "box_01"})],
        "box_01 is green according to bot_03, which I trust more because it is newer.",
        "bot_03 reported green 10 min ago and bot_02 reported blue 1 h ago; I trust green from bot_03 more "
        "because it is newer.",
    ])
    agent = Agent(world.tools, llm)
    result = agent.ask("What color is box_01?")
    checks = [s["text"] for s in result.trace if s["type"] == "self_check"]
    assert len(checks) == 1 and "leaves out blue" in checks[0]
    assert "blue" in result.answer


def test_self_check_requires_looking_at_all_records_about_a_named_entity():
    world = build_world(load_scenario("B1"))  # memory also has bot_02's colour record for box_01
    llm = ScriptedLLM([
        [("query_beliefs", {"entity": "box_01", "property": "located_at"})],
        "box_01 is in Room_101.",
        [("query_beliefs", {"entity": "box_01"}), ("read_camera", {})],
        "box_01 is in Room_101.",
        "box_01 is in Room_101.",
        "box_01 is in Room_101.",
    ])
    agent = Agent(world.tools, llm, self_check=True)
    result = agent.ask("Where is box_01?")
    checks = [s["text"] for s in result.trace if s["type"] == "self_check"]
    assert checks and "not looked at" in checks[0] and "color from agent:bot_02" in checks[0]


def test_a_no_record_note_does_not_count_as_evidence():
    world = build_world(load_scenario("H1"))
    llm = ScriptedLLM([
        [("query_beliefs", {}), ("get_provenance", {"entity": "crate_07"}), ("read_camera", {})],
        "The camera shows crate_07 is blue.",
        "I have no record of crate_07, so I don't know its colour.",
    ])
    result = Agent(world.tools, llm).ask("What color is crate_07 in Room 303?")
    assert any("crate_07" in s["text"] for s in result.trace if s["type"] == "self_check")


def test_disagreeing_records_are_listed_newest_first():
    world = build_world(load_scenario("B3"))
    data = json.loads(world.tools.execute("query_beliefs", {"entity": "box_01"}))["data"]
    d = data["disagreements"][0]
    assert [x["value"] for x in d["newest_first"]] == ["green", "blue"]
    assert d["newest"] == "green from bot_03_log (10 min ago)"


def test_user_beliefs_are_not_treated_as_evidence_in_disagreements():
    world = build_world(load_scenario("B1"))
    world.tools.execute("record_user_belief", {"entity": "box_01", "property": "color", "value": "red",
                                               "evidence": "find the red box"})
    data = json.loads(world.tools.execute("query_beliefs", {"entity": "box_01"}))["data"]
    assert "disagreements" not in data


def test_ablation_switches_turn_safeguards_off():
    from i_agent.evaluation import level_options
    tools, self_check = level_options("plain")
    world = build_world(load_scenario("A1"), **tools)
    data = json.loads(world.tools.execute("read_lidar", {"direction": "front"}))["data"]
    assert "memory_check" not in data and world.tools.actionable_conflicts() == []
    out = json.loads(world.tools.execute("update_belief", {
        "entity": "route_A", "property": "status", "value": "purple", "source": "lidar_front",
        "confidence": 0.9, "reason": "x"}))
    assert out["ok"] is True and self_check is False   # no grounded-write guard at this level


def test_sensors_level_exposes_only_sensor_tools():
    from i_agent.evaluation import level_options
    tools, _ = level_options("sensors")
    world = build_world(load_scenario("A1"), **tools)
    assert sorted(world.tools.names) == ["get_pose", "move", "read_camera", "read_lidar"]
    assert sorted(t["function"]["name"] for t in world.tools.schemas) == sorted(world.tools.names)


def test_levels_run_end_to_end_with_a_scripted_model():
    from i_agent.evaluation import run_scenario
    for level in ("baseline", "sensors", "plain", "checks", "full"):
        llm = ScriptedLLM([[("read_lidar", {"direction": "front"})], "It is blocked."] + ["It is blocked."] * 6)
        rec = run_scenario(load_scenario("A1"), llm, level=level)
        assert rec["mode"] == level and rec["set"] == "dev"


def test_python_style_tool_calls_are_parsed():
    calls, rest = extract_text_tool_calls('Checking now: query_beliefs(entity="crate_07") and get_pose().',
                                          ["query_beliefs", "get_pose"])
    assert [(c["name"], json.loads(c["arguments"])) for c in calls] == [
        ("query_beliefs", {"entity": "crate_07"}), ("get_pose", {})]
    assert "query_beliefs" not in rest
