# Results: heldout2 set, level full, qwen2.5:7b, temperature 0, 3 runs per scenario (rescored 2026-11-15 22:19)

Overall: 25/33 runs passed all checks

| scenario | type | pass_rate | answer | tools | memory | grounding | most_common_failure |
|---|---|---|---|---|---|---|---|
| NA1_back_route_blocked | A | 3/3 | 3/3 | 3/3 | 3/3 | - |  |
| NA2_drive_request_clear | A | 3/3 | 3/3 | 3/3 | 3/3 | - |  |
| NA3_spike_says_clear | A | 3/3 | 3/3 | 3/3 | 3/3 | - |  |
| NA4_report_vs_camera_dim | A | 0/3 | 0/3 | 3/3 | 3/3 | - | mentions one of ['not here', 'not in this room', 'not in room', 'not present', 'cannot see', "can't see", "don't see", 'do not see', 'not visible', 'not detect', 'did not detect', "didn't detect", "isn't here", 'is not here', 'is not in', "isn't in", 'not currently in', 'not found'] |
| NB1_user_insists_green | B | 3/3 | 3/3 | 3/3 | 3/3 | - |  |
| NB2_laptop_moved | B | 3/3 | 3/3 | 3/3 | 3/3 | - |  |
| NB3_two_reports_location | B | 3/3 | 3/3 | 3/3 | 3/3 | - |  |
| NH1_unknown_robot_report | grounding | 3/3 | 3/3 | 3/3 | - | - |  |
| NH2_unknown_chair_colour | grounding | 3/3 | 3/3 | 3/3 | - | 3/3 |  |
| NP1_who_when_why | provenance | 0/3 | 0/3 | 3/3 | - | - | mentions one of ['patrol', 'security'] |
| NP2_why_downgraded_left | provenance | 1/3 | 3/3 | 3/3 | 1/3 | - | route_L.status [self] state |
