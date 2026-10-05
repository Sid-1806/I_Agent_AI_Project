"""Every scenario file is valid and builds a working world. Owner: Udit"""
import hashlib
import re
from pathlib import Path

import pytest

from i_agent.scenario import SCENARIO_DIR, all_scenarios, build_world, load_scenario

DEV = all_scenarios("dev")
HELDOUT = all_scenarios("heldout")


def test_each_set_has_ten_scenarios_and_ids_are_unique_across_sets():
    assert len(DEV) == 10 and len(HELDOUT) == 10
    ids = [s["id"] for s in DEV + HELDOUT]
    assert len(set(ids)) == 20


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


def test_heldout_files_match_their_frozen_hashes():
    frozen = (SCENARIO_DIR / "heldout" / "FROZEN.md").read_text(encoding="utf-8")
    expected = {name: digest for digest, name in re.findall(r"`([0-9a-f]{64})`\s+`([^`]+\.json)`", frozen)}
    assert len(expected) == 10
    for name, digest in expected.items():
        data = (SCENARIO_DIR / "heldout" / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == digest, f"{name} changed after it was frozen"
