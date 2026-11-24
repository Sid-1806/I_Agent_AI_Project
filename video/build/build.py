"""Build video/I_Agent_video.mp4 from video/stills with Windows text-to-speech narration.

    python video/build/build.py

Uses only software already on Windows: the OneCore voices for narration and PowerPoint's own
video export. One slide per still, with its narration and a duration equal to the narration.
"""
import json
import subprocess
import wave
from pathlib import Path

HERE = Path(__file__).parent
VIDEO = HERE.parent
AUDIO = HERE / "audio"
VOICE = {"Siddh": "Ravi", "Rudraksh": "Mark", "Udit": "David"}
PAUSE = 0.5  # seconds of silence after each line

# (still, speaker, words) in order; this is the text of video/SCRIPT.md, split per still.
LINES = [
    ("01_title", "Siddh", "We're Null Pointers. This is I, Agent: keeping an L L M agent honest about what it actually knows."),
    ("02_layers", "Siddh", "On its own, an L L M will happily trust a day-old map. So we split the robot into three layers: "
                           "memory, a belief graph with a history log; a brain, a seven-billion-parameter model; and a "
                           "simulated world with a LiDAR and a camera. The brain reaches the other two only through tools, "
                           "so every claim must come from a tool result."),
    ("03_ui_live", "Rudraksh", "Here's our interface: the world on the left, memory below it, and the agent's steps on the right."),
    ("04_a1_question", "Rudraksh", "Scenario A. The map says the route is clear. We ask: is it?"),
    ("05_a1_first_scan", "Rudraksh", "The LiDAR sees an obstacle twelve centimetres ahead."),
    ("06_a1_self_check", "Rudraksh", "The first draft trusts that one reading. Our self-check rejects it: one reading could be noise."),
    ("07_a1_second_scan", "Siddh", "Every reading updates the map's confidence, weighted by how reliable the sensor is: from one "
                                   "to zero point eight four, then to zero point two after a second scan. Nothing is deleted; "
                                   "the history stays."),
    ("08_a1_answer", "Rudraksh", "Only then does it answer: no, the route is blocked."),
    ("09_b1_user_belief", "Udit", "Scenario B is about whose belief is whose. The user asks for the red box. The agent stores "
                                  "that as the user's belief, not as a fact."),
    ("10_b1_camera", "Udit", "Under yellow light, the camera sees brown. The true colour, blue, is drawn on our map, but the "
                             "agent never sees it."),
    ("12_b1_answer", "Udit", "Memory keeps all three apart: the user says red, the camera sees brown, and another robot's log "
                             "says blue. The agent reports each one separately."),
    ("13_results", "Udit", "On eleven scenarios we never tuned on, the same model gets 45 percent right on its own, and 82 "
                           "percent with our layers. Counting only answers also backed by real tool calls, it goes from zero "
                           "to 76 percent. After fixing what those runs exposed, all 34 completed runs pass."),
    ("14_team", "Siddh", "Siddh built the memory layer, Rudraksh the brain, and Udit the world and evaluation. Thank you."),
]


def main() -> None:
    AUDIO.mkdir(exist_ok=True)
    items = [{"id": still, "voice": VOICE[who], "text": text} for still, who, text in LINES]
    (HERE / "lines.json").write_text(json.dumps(items, indent=1), encoding="utf-8")
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(HERE / "tts.ps1"),
                    "-Lines", str(HERE / "lines.json"), "-OutDir", str(AUDIO)], check=True)
    plan, total = [], 0.0
    for still, who, _ in LINES:
        wav = AUDIO / f"{still}.wav"
        with wave.open(str(wav)) as w:
            seconds = w.getnframes() / w.getframerate()
        slide = round(seconds + PAUSE, 2)
        total += slide
        plan.append({"image": str(VIDEO / "stills" / f"{still}.png"), "audio": str(wav), "seconds": slide})
        print(f"{still:20} {who:9} {slide:5.1f}s")
    print(f"total {total:.1f}s")
    if total > 175:
        raise SystemExit("narration is too long for a 3-minute video")
    (HERE / "plan.json").write_text(json.dumps(plan, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
