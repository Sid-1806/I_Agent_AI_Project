# Results: dev set, level checks, qwen2.5:7b, temperature 0, 1 runs per scenario (rescored 2026-11-15 22:18)

Overall: 4/10 runs passed all checks

| scenario | type | pass_rate | answer | tools | memory | grounding | most_common_failure |
|---|---|---|---|---|---|---|---|
| A1_route_blocked | A | 0/1 | 1/1 | 0/1 | 0/1 | - | called update_belief |
| A2_route_reopened | A | 0/1 | 0/1 | 0/1 | 0/1 | - | mentions one of ['is clear', 'now clear', 'currently clear', 'route is clear', 'path is clear', 'is open', 'is free', 'yes'] |
| A3_noisy_lidar | A | 0/1 | 1/1 | 0/1 | 1/1 | - | called read_lidar at least 2x |
| A4_object_missing | A | 0/1 | 1/1 | 0/1 | 0/1 | - | called update_belief |
| A5_stale_belief | A | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| B1_three_colors | B | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 |  |
| B2_false_belief | B | 0/1 | 1/1 | 0/1 | 0/1 | - | called record_user_belief |
| B3_conflicting_reports | B | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 |  |
| H1_unknown_object | grounding | 0/1 | 0/1 | 0/1 | - | 1/1 | mentions one of ["don't know", 'do not know', 'no record', 'no records', 'no information', 'unknown', 'cannot determine', "can't determine", 'no data', "don't have", 'do not have', 'not able', 'unable', 'no memory record', 'cannot provide', "can't provide", 'no sensor reading', 'not aware'] |
| P1_provenance | provenance | 1/1 | 1/1 | 1/1 | - | - |  |
