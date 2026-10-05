# Scenario format

Each file is one test case and is the project's "data".

```jsonc
{
  "id": "A1_route_blocked",
  "type": "A",                      // A = groundedness, B = perspective, grounding, provenance
  "owner": "Udit",
  "description": "...",
  "world": {                        // ground truth, only visible through sensors
    "robot":   {"room": "Room_101", "facing": {"front": "route_A"}},
    "routes":  {"route_A": {"from": "Room_101", "to": "Room_102", "length_cm": 800, "obstacle_cm": 12}},
    "objects": {"box_01": {"type": "box", "room": "Room_101", "color": "blue"}},
    "lighting": {"Room_101": "yellow"},
    "lidar_script": {"route_A": [9, 240, 245]}          // optional scripted noise
  },
  "memory": [                       // initial beliefs; age_s = how long ago they were recorded
    {"subject": "route_A", "predicate": "status", "obj": "clear", "perspective": "map",
     "source": "Default_Map", "confidence": 1.0, "age_s": 86400, "reason": "optional provenance note"}
  ],
  "turns": ["user message 1", "user message 2"],
  "expect": { ... }                 // see i_agent/evaluation.py for every option
}
```

To add a scenario, copy an existing file, give it the next number, and run
`python -m pytest tests/test_scenarios.py` (update the expected count there) and
`python run_scenario.py <id>`.
