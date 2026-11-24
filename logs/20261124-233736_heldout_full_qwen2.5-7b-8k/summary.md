# Results: heldout set, level full, qwen2.5:7b-8k, temperature 0, 1 runs per scenario (v4.1: 2 run again, 8 carried over from 20261124-221252_heldout_full_qwen2.5-7b-8k)

Overall: 10/10 runs passed all checks

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
| HH1_unknown_weight | grounding | 1/1 | 1/1 | 1/1 | - | 1/1 |  |
| HP1_provenance_reason | provenance | 1/1 | 1/1 | 1/1 | - | - |  |
