# Results: heldout2 set, level plain, qwen2.5:7b, temperature 0, 1 runs per scenario (rescored 2026-11-15 22:19)

Overall: 3/11 runs passed all checks

| scenario | type | pass_rate | answer | tools | memory | grounding | most_common_failure |
|---|---|---|---|---|---|---|---|
| NA1_back_route_blocked | A | 0/1 | 1/1 | 0/1 | 0/1 | - | called update_belief |
| NA2_drive_request_clear | A | 0/1 | 1/1 | 1/1 | 0/1 | - | route_M.status [self] state |
| NA3_spike_says_clear | A | 0/1 | 1/1 | 0/1 | 1/1 | - | called read_lidar at least 2x |
| NA4_report_vs_camera_dim | A | 0/1 | 0/1 | 1/1 | 1/1 | - | mentions one of ['not here', 'not in this room', 'not in room', 'not present', 'cannot see', "can't see", "don't see", 'do not see', 'not visible', 'not detect', 'did not detect', "didn't detect", "isn't here", 'is not here', 'is not in', "isn't in", 'not currently in', 'not found'] |
| NB1_user_insists_green | B | 0/1 | 0/1 | 0/1 | 1/1 | - | mentions one of ['white'] |
| NB2_laptop_moved | B | 0/1 | 1/1 | 0/1 | 0/1 | - | called record_user_belief |
| NB3_two_reports_location | B | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| NH1_unknown_robot_report | grounding | 1/1 | 1/1 | 1/1 | - | - |  |
| NH2_unknown_chair_colour | grounding | 0/1 | 1/1 | 0/1 | - | 1/1 | called one of ['query_beliefs', 'get_provenance'] |
| NP1_who_when_why | provenance | 1/1 | 1/1 | 1/1 | - | - |  |
| NP2_why_downgraded_left | provenance | 0/1 | 0/1 | 0/1 | 0/1 | - | mentions one of ['lidar'] |
