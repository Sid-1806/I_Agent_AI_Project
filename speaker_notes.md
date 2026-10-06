# I, Agent: mid-sem flash talk, speaker notes

Not included in the PPT. Total about 3.5 minutes.

## Slide 1: Problem and Approach

**PRESENTER 1 · about 70 seconds**

Our project is I, Agent: a three-layer architecture that makes an LLM agent stay grounded in what it actually knows.

Here's the problem in one example. Same question, same model, same memory. The robot's map, which is a day old, says route A is clear. But the LiDAR now sees an obstacle 12 centimetres ahead. If we just give the model its memory as text, it answers "Yes, my route is clear." That's a real answer from our test, and it's wrong.

With our layers, the same model says the route is blocked, and that it lowered its trust in the old map to 0.3.

The difference is the design on the right. We split the robot into three layers: memory, the brain, and the world. Memory is a belief graph in NetworkX plus a log in SQLite of where every belief came from. The brain is qwen2.5, a 7-billion-parameter open-weight model running locally. The world is a simulated building with a LiDAR, a camera and a bumper. The key rule is that the brain can only reach the other two layers through tools, so every claim it makes has to come from a memory record or a sensor reading.

Our data is 20 test scenarios we wrote ourselves: 10 we developed against, and 10 we froze before ever running the agent on them.

**IF ASKED**
• Why not Llama? The proposal suggests Llama-3-8B, but our cloud provider dropped it, so we use qwen2.5:7b, which is the same size and also open-weight.
• Why separate layers? So every fact in an answer can be traced to a tool call, and so each layer can be tested on its own.

## Slide 2: Milestones and Results

**PRESENTER 2 · about 100 seconds**

Three of the four milestones in our proposal are done: the layers and the data formats between them, the tool-calling loop, and Scenario A. Milestone 4, Scenario B, is in progress.

On the left are the tests, run on the full system.

Scenario A is about trusting a live sensor over a stale map. A1 is the case from the first slide. A2 is the reverse: the map says blocked but the route is now clear. In A3 the LiDAR gives one fake reading, and the agent has to read again before believing it. In A4 the map says a box is in the room, but the camera can't see it. In A5 the agent's own belief is two hours old. All five pass.

Scenario B is about keeping track of whose belief is whose. In B1 the user thinks a box is red, the camera sees brown because of yellow lighting, and another robot's log says it was painted blue; the agent keeps all three apart. B2 is a false-belief test: the user doesn't know the box was moved. Both pass. B3 fails: when two robots disagree, the agent picks the newer report but never mentions the older one. That's what we're fixing next.

On the right is a real run of A1. Before: the map says route A is clear. After: the agent read the LiDAR twice, saved "blocked" with the LiDAR as its source, and kept the old map belief but downgraded it from 1 to 0.3. Nothing is deleted, so the agent can always explain why it changed its mind.

**IF ASKED**
• How many runs? Each scenario was run 6 times on the final system. A2 and B1 each failed once; B3 failed all 6.
• Does it work on new cases? On the 10 frozen held-out scenarios, Scenario A got 15 out of 15 right; Scenario B only 3 out of 8.
• What do the layers add? With no tools, the same model gets Scenario A right only 40% of the time on our scenarios, and 20% on the held-out ones. Only the full system gets every one right.
• How did you get here? We ran the dev scenarios after each round of fixes: 4, then 6, 7 and 8 out of 10 passed. The model kept claiming updates it never made, and once saved an invented fact, so memory now rejects values it never observed and a self-check verifies each answer.
• How was the graph made? Our graph_snapshot.py script draws it straight from the run's log file.

## Slide 3: Contributions

**PRESENTER 2 · about 25 seconds**

Finally, who did what. Siddh built the memory layer: what the robot believes and the history of how each belief changed. Rudraksh built the brain: the LLM loop, its tools, and the safeguards that stop it claiming things it didn't do. Udit built the simulated world and the evaluation: the test scenarios and the automatic checks.

The code was written with an AI coding assistant.

Thank you.

**IF ASKED**
• What's next? Finish Scenario B, starting with B3; build a larger test set; and write the architecture verification report.
• Siddh's details: belief graph with one edge per viewpoint, SQLite provenance log, the conflict rule (map confidence × 0.3), before/after snapshots.
• Rudraksh's details: ReAct loop on qwen2.5:7b, 8 tools and the system prompt, the self-check, grounded memory writes, fixes for small-model tool-call errors.
• Udit's details: LiDAR noise and lighting effects, 20 scenarios including 10 held out, four automatic checks with a no-tools baseline, the results report and demo scripts.
