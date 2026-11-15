# 20261005-225643_heldout_full_qwen2.5-7b_t0.7 (rescored 2026-11-15 22:19)

Overall: 9/12 runs passed all checks

| scenario | type | pass_rate | answer | tools | memory | grounding | most_common_failure |
|---|---|---|---|---|---|---|---|
| HA1_right_route_blocked | A | 2/2 | 2/2 | 2/2 | 2/2 | - |  |
| HA2_left_route_reopened | A | 1/2 | 2/2 | 2/2 | 1/2 | - | route_E.status [self] state |
| HA3_noisy_left_scan | A | 2/2 | 2/2 | 2/2 | 2/2 | - |  |
| HA4_crate_missing_dim_room | A | 2/2 | 2/2 | 2/2 | 2/2 | - |  |
| HA5_crate_found_elsewhere | A | 2/2 | 2/2 | 2/2 | 2/2 | - |  |
| HB1_cup_dim_light | B | 0/2 | 0/2 | 1/2 | 1/2 | 2/2 | mentions one of ['dark green'] |
