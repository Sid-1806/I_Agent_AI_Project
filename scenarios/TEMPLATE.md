# Writing new test scenarios (without reading the code)

The strongest test of the agent is a set of scenarios written by someone who has **not** looked at
`i_agent/`, the prompts, or the existing scenarios. If that is you: please don't open those files.
Everything you need is on this page.

## What a scenario is

One JSON file describes a small world (the truth), what the robot remembers at the start (which may
be wrong or out of date), the user's questions, and how to check the answer automatically.

```json
{
  "id": "IX1_short_name",
  "type": "A",
  "description": "One or two sentences: the situation and what a good agent should do.",
  "world": {
    "robot": {"room": "Room_301", "facing": {"front": "route_X"}},
    "routes": {"route_X": {"from": "Room_301", "to": "Room_302", "length_cm": 700, "obstacle_cm": 25}},
    "objects": {"mug_04": {"type": "cup", "room": "Room_301", "color": "white"}},
    "lighting": {"Room_301": "normal"}
  },
  "memory": [
    {"subject": "route_X", "predicate": "status", "obj": "clear", "perspective": "map",
     "source": "Default_Map", "confidence": 1.0, "age_s": 86400}
  ],
  "turns": ["Can you drive along route_X right now?"],
  "expect": {
    "answer_mentions": [["blocked", "obstacle"]],
    "tools_required": ["read_lidar"],
    "beliefs": [{"subject": "route_X", "predicate": "status", "perspective": "self", "value": "blocked"}]
  }
}
```

`type` is one of `A` (sensor vs stale memory), `B` (whose belief is whose), `grounding` (the right
answer is "I don't know") or `provenance` (who/when/why a belief was recorded).

## What the simulated world can do

- **Rooms and routes.** The robot is in one room. `facing` says which route lies in each direction
  (`front`, `back`, `left`, `right`). A route goes `from` one room `to` another, is `length_cm` long,
  and may have an obstacle at `obstacle_cm`.
- **LiDAR** (per direction) reports the distance to the nearest obstacle on that route, or the route
  length if there is none. Under 50 cm counts as **blocked**. To fake noise, add
  `"lidar_script": {"route_X": [9, 240, 245]}` to `world`: successive readings, the last one repeating.
- **Camera** sees only the robot's current room: each object there with its perceived colour.
  `lighting` can be `normal`, `yellow` (blue looks brown, red orange, white yellow, green olive,
  grey beige) or `dim` (blue looks black, red maroon, green dark green, white grey).
- **Driving** along a blocked route hits the bumper; otherwise the robot arrives in the next room.
- Object `type` can be `box`, `crate`, `cup`, `laptop`, `keys`, `bin`, `chair` (others work too).
- Entity ids are lowercase with an underscore and a number (`crate_12`, `route_X`); rooms are
  `Room_<number>`.

## What the robot can remember

Each memory entry is a belief: `subject` (thing), `predicate` (property: `status`, `color`,
`located_at`, ...), `obj` (value), `perspective`, `source`, `confidence` (0 to 1) and `age_s`
(seconds since it was recorded). Perspectives:

- `map`: the static baseline map (`source` like `Default_Map`), often stale;
- `agent:bot_07`: a report logged by another robot (`source` like `bot_07_log`); you can add a
  `"reason"`, such as "bot_07 moved crate_08 to Room_150";
- `self`: the robot's own belief (`source` like `lidar_front` or `mission_plan`; a planned route is
  `{"subject": "robot", "predicate": "planned_route", "obj": "route_X", "perspective": "self", ...}`);
- `user` beliefs are not loaded from memory: the user states them in a question.

## Ideas worth testing

- **A:** the map or an old report is wrong, and a sensor can show it.
- **B:** the user believes something false, the camera is fooled by lighting, or two robots disagree;
  the answer should keep the views apart.
- **Unknowns:** ask about something nothing in memory or in sensor range covers.
- **Provenance:** ask who reported something, when, or why.
- Multi-turn questions (several strings in `turns`) and unusual wordings are welcome.

## How to write the checks (`expect`)

| Field | Meaning |
|---|---|
| `answer_mentions` | list of groups; the final answer must contain at least one phrase from each group |
| `answer_excludes` | phrases the final answer must not contain |
| `tools_required` | tools that must be called: `query_beliefs`, `get_provenance`, `update_belief`, `record_user_belief`, `read_lidar`, `read_camera`, `get_pose`, `move` |
| `tools_any` | groups; at least one tool from each group must be called |
| `tool_min_counts` | e.g. `{"read_lidar": 2}` |
| `tools_forbidden` | tools that must not be executed |
| `beliefs` | the memory's final state: `subject`, `predicate`, `perspective`, and one of `value`, `value_not`, `value_contains`, `min_confidence`, `max_confidence` |
| `grounded_vocab` | words (e.g. colours) the answer may use only if a tool result or the user mentioned them |

Phrases match whole words, ignoring case; give several phrasings in a group where a correct answer
could word it differently. Write the checks from what a good answer must contain, not from what you
expect this particular agent to say.

## Freezing them (before anyone runs the agent on them)

1. Put the files in a new folder, e.g. `scenarios/heldout3/`, named `01_IX1_short_name.json`, ...
2. Run `python scenarios/freeze.py heldout3`. It writes `FROZEN.md` with each file's SHA-256.
3. Commit the folder before any run, so the commit time proves the tests came first.
4. Add the folder's name to `SETS` in `i_agent/scenario.py`, then run
   `python evaluate.py --set heldout3 --runs 3 --provider ollama --model qwen2.5:7b-8k`.

Never edit a frozen file afterwards. If a scenario turns out to be wrong, say so and leave it in.
