"""Tests for the declarative layer. Owner: Siddh"""
from i_agent.clock import SimClock
from i_agent.declarative import BeliefStore, source_kind
from i_agent.schemas import Belief


def make_store():
    store = BeliefStore(SimClock())
    store.load([Belief(subject="route_A", predicate="status", obj="clear", perspective="map",
                       source="Default_Map", confidence=1.0, timestamp=store.clock.now() - 100)])
    return store


def test_query_and_get():
    store = make_store()
    assert store.get("route_A", "status", "map").obj == "clear"
    assert store.get("route_A", "status", "self") is None
    assert len(store.query(subject="route_A")) == 1
    assert store.query(subject="nothing") == []


def test_perspectives_coexist():
    store = make_store()
    t = store.clock.now()
    store.assert_belief(Belief(subject="box_01", predicate="color", obj="red", perspective="user",
                               source="user_utterance", confidence=1.0, timestamp=t))
    store.assert_belief(Belief(subject="box_01", predicate="color", obj="blue", perspective="agent:bot_02",
                               source="bot_02_log", confidence=0.9, timestamp=t))
    colors = {b.perspective: b.obj for b in store.query("box_01", "color")}
    assert colors == {"user": "red", "agent:bot_02": "blue"}


def test_each_contradicting_reading_lowers_the_map_by_the_sensors_reliability():
    store = make_store()  # map: route_A clear, confidence 1.0
    first = store.update_with_evidence("route_A", "status", "blocked", 0.95, "lidar_front")
    assert first[0]["new_confidence"] == 0.839       # 0.99 in odds x (0.05 / 0.95): one reading barely moves it
    store.update_with_evidence("route_A", "status", "blocked", 0.95, "lidar_front")
    assert store.get("route_A", "status", "map").confidence == 0.215   # two agreeing readings move it a lot
    history = store.get_provenance("route_A")
    assert [h.reason for h in history][0] == "initial load"
    assert "reliability 0.95" in history[-1].reason and "contradicted" in history[-1].reason


def test_a_spike_is_undone_by_the_readings_after_it():
    store = make_store()
    store.update_with_evidence("route_A", "status", "blocked", 0.95, "lidar_front")   # spurious
    store.update_with_evidence("route_A", "status", "clear", 0.95, "lidar_front")
    assert store.get("route_A", "status", "map").confidence == 0.99


def test_a_less_reliable_sensor_moves_the_map_less():
    a, b = make_store(), make_store()
    a.update_with_evidence("route_A", "status", "blocked", 0.95, "camera")
    b.update_with_evidence("route_A", "status", "blocked", 0.82, "camera")
    assert b.get("route_A", "status", "map").confidence > a.get("route_A", "status", "map").confidence


def test_writing_a_belief_does_not_change_the_map():
    store = make_store()
    store.assert_belief(Belief(subject="route_A", predicate="status", obj="blocked",
                               source="lidar_front", confidence=0.95, timestamp=store.clock.now()))
    assert store.get("route_A", "status", "self").obj == "blocked"
    assert store.get("route_A", "status", "map").confidence == 1.0


def test_older_records_count_for_less():
    store = make_store()
    now = store.clock.now()
    old = Belief(subject="box_01", predicate="color", obj="blue", perspective="agent:bot_02",
                 source="bot_02_log", confidence=0.9, timestamp=now - 3600)
    new = Belief(subject="box_01", predicate="color", obj="green", perspective="agent:bot_03",
                 source="bot_03_log", confidence=0.85, timestamp=now - 600)
    user = Belief(subject="box_01", predicate="color", obj="red", perspective="user",
                  source="user_utterance", confidence=1.0, timestamp=now - 86400)
    assert store.weighted_confidence(old) == 0.636      # 0.9 x 0.5 ** (1 h / 2 h)
    assert store.weighted_confidence(new) == 0.802
    assert store.weighted_confidence(user) == 1.0       # what the user thinks does not decay


def test_user_and_agent_beliefs_are_never_downgraded():
    store = make_store()
    t = store.clock.now()
    store.assert_belief(Belief(subject="box_01", predicate="color", obj="blue", perspective="agent:bot_02",
                               source="bot_02_log", confidence=0.9, timestamp=t))
    store.assert_belief(Belief(subject="box_01", predicate="color", obj="brown", source="camera",
                               confidence=0.8, timestamp=t))
    assert store.get("box_01", "color", "agent:bot_02").confidence == 0.9


def test_snapshots_and_diff():
    store = make_store()
    v1 = store.snapshot("before")
    store.assert_belief(Belief(subject="route_A", predicate="status", obj="blocked",
                               source="lidar_front", confidence=0.95, timestamp=store.clock.now()))
    store.update_with_evidence("route_A", "status", "blocked", 0.95, "lidar_front")
    v2 = store.snapshot("after")
    diff = store.diff(v1, v2)
    assert any(line.startswith("+ route_A.status [self] = blocked") for line in diff)
    assert any(line.startswith("~ route_A.status [map]") for line in diff)


def test_source_kind():
    assert source_kind("lidar_front") == "sensor"
    assert source_kind("camera") == "sensor"
    assert source_kind("Default_Map") == "map"
    assert source_kind("bot_02_log") == "agent"
