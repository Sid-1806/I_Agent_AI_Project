# Results: heldout set, level full, qwen2.5:7b-8k, temperature 0, 1 runs per scenario

Overall: 9/10 runs passed all checks

| scenario | type | pass_rate | answer | tools | memory | grounding | most_common_failure |
|---|---|---|---|---|---|---|---|
| HA1_right_route_blocked | A | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| HA2_left_route_reopened | A | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| HA3_noisy_left_scan | A | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| HA4_crate_missing_dim_room | A | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| HA5_crate_found_elsewhere | A | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| HB1_cup_dim_light | B | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 |  |
| HB2_keys_moved | B | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| HB3_three_robot_reports | B | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 |  |
| HH1_unknown_weight | grounding | 0/1 | 0/1 | 1/1 | - | 1/1 | mentions one of ["don't know", 'do not know', 'no record', 'no records', 'no information', 'unknown', 'cannot determine', "can't determine", 'no data', "don't have", 'do not have', 'not able', 'unable', 'no memory record', 'cannot provide', "can't provide", 'no sensor reading', 'not aware'] |
| HP1_provenance_reason | provenance | 1/1 | 1/1 | 1/1 | - | - |  |
