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


def test_sensor_contradiction_downgrades_map_and_logs_provenance():
    store = make_store()
    summary = store.assert_belief(Belief(subject="route_A", predicate="status", obj="blocked",
                                         source="lidar_front", confidence=0.95, timestamp=store.clock.now()))
    assert store.get("route_A", "status", "self").obj == "blocked"
    assert store.get("route_A", "status", "map").confidence == 0.3
    assert summary["downgraded"][0]["new_confidence"] == 0.3
    history = store.get_provenance("route_A")
    assert [h.reason for h in history][0] == "initial load"
    assert any("downgraded" in h.reason for h in history)


def test_agreeing_sensor_does_not_downgrade_map():
    store = make_store()
    store.assert_belief(Belief(subject="route_A", predicate="status", obj="clear",
                               source="lidar_front", confidence=0.95, timestamp=store.clock.now()))
    assert store.get("route_A", "status", "map").confidence == 1.0


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
    v2 = store.snapshot("after")
    diff = store.diff(v1, v2)
    assert any(line.startswith("+ route_A.status [self] = blocked") for line in diff)
    assert any(line.startswith("~ route_A.status [map]") for line in diff)


def test_source_kind():
    assert source_kind("lidar_front") == "sensor"
    assert source_kind("camera") == "sensor"
    assert source_kind("Default_Map") == "map"
    assert source_kind("bot_02_log") == "agent"
