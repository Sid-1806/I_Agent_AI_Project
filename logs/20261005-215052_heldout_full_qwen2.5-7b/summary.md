# Results: heldout set, level full, qwen2.5:7b, temperature 0, 3 runs per scenario (rescored 2026-11-15 22:18)

Overall: 20/30 runs passed all checks

| scenario | type | pass_rate | answer | tools | memory | grounding | most_common_failure |
|---|---|---|---|---|---|---|---|
| HA1_right_route_blocked | A | 3/3 | 3/3 | 3/3 | 3/3 | - |  |
| HA2_left_route_reopened | A | 1/3 | 3/3 | 3/3 | 1/3 | - | route_E.status [self] state |
| HA3_noisy_left_scan | A | 2/3 | 3/3 | 3/3 | 2/3 | - | route_G.status [self] state |
| HA4_crate_missing_dim_room | A | 3/3 | 3/3 | 3/3 | 3/3 | - |  |
| HA5_crate_found_elsewhere | A | 3/3 | 3/3 | 3/3 | 3/3 | - |  |
| HB1_cup_dim_light | B | 0/3 | 0/3 | 1/3 | 1/3 | 2/3 | mentions one of ['white'] |
| HB2_keys_moved | B | 0/3 | 1/2 | 1/2 | 1/2 | - | mentions one of ['112'] |
| HB3_three_robot_reports | B | 2/3 | 2/3 | 3/3 | 3/3 | 3/3 | mentions one of ['orange'] |
| HH1_unknown_weight | grounding | 3/3 | 3/3 | 3/3 | - | 3/3 |  |
| HP1_provenance_reason | provenance | 3/3 | 3/3 | 3/3 | - | - |  |
