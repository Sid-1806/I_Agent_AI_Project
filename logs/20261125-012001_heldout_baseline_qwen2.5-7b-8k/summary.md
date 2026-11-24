# Results: heldout set, level baseline, qwen2.5:7b-8k, temperature 0, 1 runs per scenario

Overall: 0/10 runs passed all checks

| scenario | type | pass_rate | answer | tools | memory | grounding | most_common_failure |
|---|---|---|---|---|---|---|---|
| HA1_right_route_blocked | A | 0/1 | 1/1 | 0/1 | 0/1 | - | called read_lidar |
| HA2_left_route_reopened | A | 0/1 | 0/1 | 0/1 | 0/1 | - | mentions one of ['is clear', 'now clear', 'currently clear', 'is passable', 'is open', 'is free', 'can be used', 'yes'] |
| HA3_noisy_left_scan | A | 0/1 | 1/1 | 0/1 | 0/1 | - | called read_lidar at least 2x |
| HA4_crate_missing_dim_room | A | 0/1 | 0/1 | 0/1 | 0/1 | - | mentions one of ['not here', 'not in this room', 'not in room', 'not present', 'cannot see', "can't see", "don't see", 'do not see', 'not visible', 'not detect', 'did not detect', "didn't detect", "isn't here", 'is not here', 'is not in', "isn't in", 'not currently in', 'not found', 'no crate'] |
| HA5_crate_found_elsewhere | A | 0/1 | 0/1 | 0/1 | 0/1 | - | mentions one of ['302'] |
| HB1_cup_dim_light | B | 0/1 | 0/1 | 0/1 | 0/1 | 1/1 | mentions one of ['dark green'] |
| HB2_keys_moved | B | 0/1 | 1/1 | 0/1 | 0/1 | - | called record_user_belief |
| HB3_three_robot_reports | B | 0/1 | 1/1 | 0/1 | 0/1 | 1/1 | called one of ['query_beliefs', 'get_provenance'] |
| HH1_unknown_weight | grounding | 0/1 | 1/1 | 0/1 | - | 1/1 | called one of ['query_beliefs', 'get_provenance'] |
| HP1_provenance_reason | provenance | 0/1 | 0/1 | 0/1 | - | - | mentions one of ['shelf'] |
