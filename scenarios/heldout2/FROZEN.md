# Held-out set 2: frozen

Frozen on 2026-10-18 20:04 (local time), before the agent was run on any of them.

These 11 scenarios were written on 18 Oct 2026, after the mid-semester evaluation, as a second and
fresh held-out set. The first held-out set (`scenarios/heldout`) has already been run, and its
results were known while the system was being improved, so it no longer measures generalisation
cleanly. This set has not been run.

They cover the same five behaviours as the dev set (A: live sensor vs stale memory, B: separate
perspectives, H: saying "I don't know", P: provenance) with new rooms, objects, directions, robots
and wordings, plus the newer behaviours added to dev on the same day: driving requests, another
robot's report contradicted by the camera, a user insisting on a false fact, and asking why a
belief was downgraded.

## Rules

1. These files must not change. `tests/test_scenarios.py` fails if any hash below stops matching.
2. No code or prompt changes are made because of results on this set. If the system changes later
   for other reasons, results on this set are reported separately for each version.
3. The git commit that adds this file is the timestamp proof that the tests existed before any
   results on them.

Caveat: these scenarios were written with the same AI coding assistant that wrote the system, so
they are not fully independent. Scenarios written by teammates who have not read the code would be
a stronger test.

## SHA-256 of each file

- `977775cba4225fd6608fe97e77f8e12db4a41f9587ca4488885272b1114f0aaf`  `01_NA1_back_route_blocked.json`
- `6076660758fd87e2dc07095fb3c9cbf7819bb76c885f23717b0671c9be199ff0`  `02_NA2_drive_request_clear.json`
- `7c52be00bfce6293a19199cf416693ebaee811ca7e09bd3f6588178719d607a8`  `03_NA3_spike_says_clear.json`
- `79415f009ca4f1aa3cfe9c5624b49d07ef3b9be5784a11970cdc5b0dd1879418`  `04_NA4_report_vs_camera_dim.json`
- `e33edeb0b12df7b15ddc6ce8184b33dca71838a7978bb862f93085958852dabf`  `05_NB1_user_insists_green.json`
- `2e5871d42bfb3e0bb929bb9f401a82958e1136e7943e9b3eda8ca67e875c986c`  `06_NB2_laptop_moved.json`
- `e852f4c9b5596705267ec43a39f244e36e75d530f4f4e79b32a2cfe498c6e73c`  `07_NB3_two_reports_location.json`
- `374b2a67ee322e1bf54841eeb1fd44708f395d276f0c1d2e3cf3a4e9ef63d37a`  `08_NH1_unknown_robot_report.json`
- `02b8a77e1522f52f0b5fe51107013dd5171fda87b63f70d9b29d1bd640bd973b`  `09_NH2_unknown_chair_colour.json`
- `845d35a7cc34aa41626a9db7e27d94088b46f0b06adad30a439e63c5b359fcc3`  `10_NP1_who_when_why.json`
- `b78ef21a699be89d6697c891d5c9e802329d497f2226abc7c694ca1535177390`  `11_NP2_why_downgraded_left.json`
