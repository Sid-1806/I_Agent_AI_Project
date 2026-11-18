"""Every scenario file is valid and builds a working world. Owner: Udit"""
import hashlib
import re
from pathlib import Path

import pytest

from i_agent.scenario import SCENARIO_DIR, all_scenarios, build_world, load_scenario

DEV = all_scenarios("dev")
HELDOUT = all_scenarios("heldout")
HELDOUT2 = all_scenarios("heldout2")


def test_sets_have_the_expected_size_and_ids_are_unique_across_sets():
    assert len(DEV) == 15 and len(HELDOUT) == 10
    ids = [s["id"] for s in DEV + HELDOUT + HELDOUT2]
    assert len(set(ids)) == len(ids)


def test_short_ids_find_the_right_set():
    assert load_scenario("A1")["set"] == "dev"
    assert load_scenario("HA1")["set"] == "heldout"
    assert load_scenario("H1")["id"] == "H1_unknown_object"


@pytest.mark.parametrize("scenario", DEV + HELDOUT, ids=lambda s: s["id"])
def test_scenario_builds(scenario):
    world = build_world(scenario)
    assert scenario["turns"] and scenario["expect"]
    assert len(world.store.query()) == len(scenario["memory"])
    world.env.read_camera()
    world.env.get_pose()


@pytest.mark.parametrize("set_name, count", [("heldout", 10), ("heldout2", 11)])
def test_heldout_files_match_their_frozen_hashes(set_name, count):
    frozen = (SCENARIO_DIR / set_name / "FROZEN.md").read_text(encoding="utf-8")
    expected = {name: digest for digest, name in re.findall(r"`([0-9a-f]{64})`\s+`([^`]+\.json)`", frozen)}
    assert len(expected) == count == len(list((SCENARIO_DIR / set_name).glob("*.json")))
    for name, digest in expected.items():
        data = (SCENARIO_DIR / set_name / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == digest, f"{name} changed after it was frozen"


def test_a_logged_run_replays_exactly():
    from i_agent.replay import replay
    logs = sorted(Path("logs").glob("20261018-204741_dev_full_*/A1_route_blocked_run1.json"))
    if not logs:
        pytest.skip("log not present")
    run = replay(logs[0])
    assert run["mismatches"] == 0  # the world replays exactly
    assert run["frames"][0]["type"] == "start" and run["frames"][-1]["type"] == "answer"
    last = {(b["s"], b["p"], b["persp"]): b for b in run["frames"][-1]["beliefs"]}
    assert last[("route_A", "status", "self")]["o"] == "blocked"
    assert last[("route_A", "status", "map")]["conf"] == 0.215   # two LiDAR readings, weighted (v4)
