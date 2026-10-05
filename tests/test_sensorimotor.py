"""Tests for the mock environment. Owner: Udit"""
from i_agent.sensorimotor import MockEnv

WORLD = {
    "robot": {"room": "Room_101", "facing": {"front": "route_A", "left": "route_B"}},
    "routes": {"route_A": {"from": "Room_101", "to": "Room_102", "obstacle_cm": 12},
               "route_B": {"from": "Room_101", "to": "Room_104", "length_cm": 650}},
    "objects": {"box_01": {"type": "box", "room": "Room_101", "color": "blue"}},
    "lighting": {"Room_101": "yellow"},
}


def test_lidar_blocked_and_clear():
    env = MockEnv(WORLD)
    front = env.read_lidar("front")
    assert front.sensor == "lidar_front"
    assert front.payload["status"] == "blocked" and front.payload["distance_cm"] == 12
    assert env.read_lidar("left").payload["status"] == "clear"
    assert env.read_lidar("back").payload["status"] == "no_route"


def test_lidar_script_simulates_noise():
    env = MockEnv({**WORLD, "lidar_script": {"route_A": [9, 240, 245]}})
    readings = [env.read_lidar("front").payload["distance_cm"] for _ in range(4)]
    assert readings == [9, 240, 245, 245]


def test_camera_colour_shifts_under_yellow_light():
    env = MockEnv(WORLD)
    reading = env.read_camera()
    assert reading.payload["ambient_light"] == "yellow"
    assert reading.payload["detections"][0]["perceived_color"] == "brown"


def test_move_blocked_then_allowed():
    env = MockEnv(WORLD)
    assert env.move("route_A").success is False
    assert env.move("route_B").success is True
    assert env.get_pose().payload["room"] == "Room_104"


def test_clock_advances_with_actions():
    env = MockEnv(WORLD)
    t0 = env.clock.now()
    env.read_lidar("front")
    env.move("route_B")
    assert env.clock.now() == t0 + 6


def test_world_config_is_not_mutated():
    world = {"robot": {"room": "Room_101", "facing": {}},
             "routes": {"r": {"from": "Room_101", "to": "Room_102"}}}
    MockEnv(world).move("r")
    assert world["robot"]["room"] == "Room_101"
