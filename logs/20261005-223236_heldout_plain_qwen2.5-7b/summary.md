# Results: heldout set, level plain, qwen2.5:7b, temperature 0, 1 runs per scenario (rescored 2026-11-15 22:18)

Overall: 3/10 runs passed all checks

| scenario | type | pass_rate | answer | tools | memory | grounding | most_common_failure |
|---|---|---|---|---|---|---|---|
| HA1_right_route_blocked | A | 0/1 | 1/1 | 0/1 | 0/1 | - | called update_belief |
| HA2_left_route_reopened | A | 0/1 | 1/1 | 0/1 | 0/1 | - | called update_belief |
| HA3_noisy_left_scan | A | 0/1 | 1/1 | 0/1 | 1/1 | - | called read_lidar at least 2x |
| HA4_crate_missing_dim_room | A | 0/1 | 0/1 | 0/1 | 0/1 | - | mentions one of ['not here', 'not in this room', 'not in room', 'not present', 'cannot see', "can't see", "don't see", 'do not see', 'not visible', 'not detect', 'did not detect', "didn't detect", "isn't here", 'is not here', 'is not in', "isn't in", 'not currently in', 'not found', 'no crate'] |
| HA5_crate_found_elsewhere | A | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| HB1_cup_dim_light | B | 0/1 | 0/1 | 0/1 | 1/1 | 1/1 | mentions one of ['dark green'] |
| HB2_keys_moved | B | 0/1 | 0/1 | 0/1 | 0/1 | - | mentions one of ['112'] |
| HB3_three_robot_reports | B | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 |  |
| HH1_unknown_weight | grounding | 0/1 | 1/1 | 0/1 | - | 1/1 | called one of ['query_beliefs', 'get_provenance'] |
| HP1_provenance_reason | provenance | 1/1 | 1/1 | 1/1 | - | - |  |
