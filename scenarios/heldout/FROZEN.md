# Held-out scenarios: frozen

Frozen on 2026-10-05 21:47 (local time), before the agent was run on any of them.

These 10 scenarios were written after the system was developed against the 10 dev scenarios.
They reuse the same world mechanics (routes, LiDAR, camera, lighting, robot reports) in new
combinations, directions, rooms, objects and wordings. Their purpose is to check whether results
on the dev set generalise.

## Rules

1. These files must not change. `tests/test_scenarios.py` fails if any hash below stops matching.
2. No code or prompt changes are made because of held-out results. If the system is changed
   later for other reasons, held-out results are reported separately for each version.
3. The git commit that added this file is the timestamp proof that the tests existed before any
   results on them.

Caveat: the same person wrote the system and these scenarios, so they are not fully independent.
Scenarios written by teammates who did not see the code would be a stronger test.

## SHA-256 of each file

- `46449a439f202f7c4bfb0c1b5afaf109df94c36417061d9ce4f73caab99f33a9`  `01_HA1_right_route_blocked.json`
- `e0f46f4e1e4cb6e8c326293d4f4cf56f831ebed82d88cfe523c4f311c8fb3fad`  `02_HA2_left_route_reopened.json`
- `7c6516c884238e51f9ee2782a3b3e837d82d15d631fffa7796811650057f9f15`  `03_HA3_noisy_left_scan.json`
- `01284765f6e8aadbd7fb3e6556a2aacc378ecc03f8ff0fe966cfc6041d49bf59`  `04_HA4_crate_missing_dim_room.json`
- `c04d93c192f299dbe97e81333fa5d3682f4dd4353548a7a27ceb91a3e7e0d9aa`  `05_HA5_crate_found_elsewhere.json`
- `d8c5e76d6a48dab380877656a46ca1346e694b4976039bd86fd5ffe95dc1d26f`  `06_HB1_cup_dim_light.json`
- `40c34be94d1757204b39ef71b36f14151adf05ebc070f349a1d96f4ce73a88d0`  `07_HB2_keys_moved.json`
- `29d8b719673181c23b4d731060ce11f97ed635eee748269cb4b01a6dd2a3e3e6`  `08_HB3_three_robot_reports.json`
- `0b8042419a2d61543822706354e4b5fb5532ba37e4eb478ea481948608dc6c75`  `09_HH1_unknown_weight.json`
- `a87c830abdd0792c8865a6c5a26ed4e7679e852f48c75810e5f001abebe9ac43`  `10_HP1_provenance_reason.json`
