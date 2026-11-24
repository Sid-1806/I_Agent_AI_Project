"""Capture the video's shots as 1920x1080 stills (needs `python server.py` running on :8000).

    python video/capture_stills.py
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
OUT = HERE / "stills"
UI = "http://localhost:8000/"
LOG = "logs/dev_iterations/20261118-145103_dev_full_qwen2.5-7b-8k/"

SHOTS = [
    ("01_title", (HERE / "cards" / "1_title.html").as_uri()),
    ("02_layers", (HERE / "cards" / "2_layers.html").as_uri()),
    ("03_ui_live", UI),
    ("04_a1_question", f"{UI}#replay={LOG}A1_route_blocked_run1.json&step=1"),
    ("05_a1_first_scan", f"{UI}#replay={LOG}A1_route_blocked_run1.json&step=2"),
    ("06_a1_self_check", f"{UI}#replay={LOG}A1_route_blocked_run1.json&step=4"),
    ("07_a1_second_scan", f"{UI}#replay={LOG}A1_route_blocked_run1.json&step=9"),
    ("08_a1_answer", f"{UI}#replay={LOG}A1_route_blocked_run1.json&step=13"),
    ("09_b1_user_belief", f"{UI}#replay={LOG}B1_three_colors_run1.json&step=2"),
    ("10_b1_camera", f"{UI}#replay={LOG}B1_three_colors_run1.json&step=8"),
    ("11_b1_self_check", f"{UI}#replay={LOG}B1_three_colors_run1.json&step=12"),
    ("12_b1_answer", f"{UI}#replay={LOG}B1_three_colors_run1.json&step=35"),
    ("13_results", (HERE / "cards" / "3_results.html").as_uri()),
    ("14_team", (HERE / "cards" / "4_team.html").as_uri()),
]

OUT.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge")
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    for name, url in SHOTS:
        page.goto("about:blank")
        page.goto(url)
        page.wait_for_timeout(3500 if url.startswith("http") else 800)
        page.screenshot(path=str(OUT / f"{name}.png"))
        print("captured", name)
    browser.close()
