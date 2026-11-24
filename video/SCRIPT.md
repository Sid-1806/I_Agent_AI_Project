# I, Agent: 3-minute video

Length **2:56** (hard limit 3:00). The finished video is `video/I_Agent_video.mp4`, narrated by Windows voices; re-record with your own voices if you prefer (see below).
Stills for every shot are in `video/stills/` (1920×1080); the app shots can also be recorded live
from the replay links below for motion (LiDAR beams, the step feed scrolling).

| Time | Speaker | On screen | Say |
|---|---|---|---|
| 0:00–0:08 | Siddh | `01_title` | "We're Null Pointers. This is I, Agent: keeping an LLM agent honest about what it actually knows." |
| 0:08–0:31 | Siddh | `02_layers` | "On its own, an LLM will trust a day-old map. So we split the robot into three layers: memory, a belief graph with a history log; a brain, a seven-billion-parameter model; and a simulated world with a LiDAR and a camera. The brain reaches the other two only through tools, so every claim must come from a tool result." |
| 0:31–0:37 | Rudraksh | `03_ui_live` | "Here's our interface: the world on the left, memory below it, and the agent's steps on the right." |
| 0:37–0:43 | Rudraksh | `04_a1_question` | "Scenario A. The map says the route is clear. We ask: is it?" |
| 0:43–0:47 | Rudraksh | `05_a1_first_scan` | "The LiDAR sees an obstacle twelve centimetres ahead." |
| 0:47–0:54 | Rudraksh | `06_a1_self_check` | "The first draft trusts that one reading. Our self-check rejects it: one reading could be noise." |
| 0:54–1:08 | Siddh | `07_a1_second_scan` | "Every reading updates the map's confidence, weighted by how reliable the sensor is: from one to zero point eight four, then to zero point two after a second scan. Nothing is deleted; the history stays." |
| 1:08–1:12 | Rudraksh | `08_a1_answer` | "Only then does it answer: no, the route is blocked." |
| 1:12–1:23 | Udit | `09_b1_user_belief` | "Scenario B is about whose belief is whose. The user asks for the red box. The agent stores that as the user's belief, not as a fact." |
| 1:23–1:33 | Udit | `10_b1_camera` | "Under yellow light, the camera sees brown. The true colour, blue, is drawn on our map, but the agent never sees it." |
| 1:33–1:42 | Udit | `11_b1_self_check` | "Its first answer forgets the other robot's report, so the self-check sends it back: name bot_02, and say what it reported." |
| 1:42–1:54 | Udit | `12_b1_answer` | "Memory keeps all three apart: the user says red, the camera sees brown, and another robot's log says blue. The agent reports each one separately." |
| 1:54–2:31 | Udit | `13_results` | "Our 36 test scenarios cover trusting sensors over a stale map, keeping perspectives apart, saying I don't know, and explaining where a belief came from. Eleven of them were frozen, with checksums, before the agent ever ran on them. On those eleven, the same model gets 45 percent right on its own, and 82 percent with our layers. Counting only answers also backed by real tool calls, it goes from zero to 76 percent. After fixing what those runs exposed, all 34 completed runs pass." |
| 2:31–2:48 | Siddh | `15_next` | "Our limits: a small model on a laptop, a simulated world, and tests written by our own team. Next, we'll finish evaluating the weighted confidence on all 36 scenarios, and test with scenarios written by outsiders." |
| 2:48–2:56 | Siddh | `14_team` | "Siddh built the memory layer, Rudraksh the brain, and Udit the world and evaluation. Thank you." |

## How to make it (about an hour)

**Recommended: Clipchamp (built into Windows 11, free).**
1. Open Clipchamp → *Create a new video* → 16:9.
2. Drag the 14 stills from `video/stills/` onto the timeline in order. Set each still's length
   to the time in the table above.
3. Each speaker records their lines: *Record & create → Audio* (or record on a phone and import
   the file). Place each clip under its stills and trim the pauses.
4. Optional, for motion: record the app itself (step 5) and swap it in for stills 04–12.
5. *Export* → 1080p. **Check the length is under 3:00** before uploading.

**Live footage of the app (optional, looks better than stills):**
```bash
python server.py
```
Open these in the browser (each opens the logged run at that step; use → / ← to step, space to
play), and record the window with **Win + Alt + R** (Xbox Game Bar) or OBS:
- A1: `http://localhost:8000/#replay=logs/dev_iterations/20261118-145103_dev_full_qwen2.5-7b-8k/A1_route_blocked_run1.json&step=1`
  (steps 2, 4, 9, 13 are the moments in the script)
- B1: `http://localhost:8000/#replay=logs/dev_iterations/20261118-145103_dev_full_qwen2.5-7b-8k/B1_three_colors_run1.json&step=2`
  (steps 8, 12, 35)

These are replays of real logged runs: the layers are rebuilt from the log, the LLM is not
called. Running the agent live takes minutes per answer on a laptop, too slow for a 3-minute video.

**Alternative: PowerPoint.** Put one still per slide, use *Record → From beginning* so each
speaker narrates their slides, then *File → Export → Create a Video* (Full HD, "use recorded
timings").

## Tips

- Rehearse once with a timer; the table adds up to 2:56, which leaves room for a slower take.
- Speak to the picture: when the number changes on screen (1 → 0.84 → 0.2), say it then.
- If asked, the numbers are in `results/results.md`: held-out set 2, system v2, temperature 0
  (full system 27/33 vs no-tools baseline 5/11; all checks 25/33 vs 0/11); v3: 34/34 completed runs.
  The B1 answer's last line says it trusts the camera more; the script only claims what it does
  get right (keeping the three views apart).
- To recapture the stills after a UI change: `python server.py`, then `python video/capture_stills.py`.
