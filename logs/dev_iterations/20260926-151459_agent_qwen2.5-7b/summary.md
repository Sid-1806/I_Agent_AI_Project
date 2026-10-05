# Results: agent, qwen2.5:7b, 1 runs per scenario

Overall: 6/10 runs passed all checks

| scenario | type | pass_rate | answer | tools | memory | grounding | most_common_failure |
|---|---|---|---|---|---|---|---|
| A1_route_blocked | A | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| A2_route_reopened | A | 0/1 | 1/1 | 0/1 | 0/1 | - | called update_belief |
| A3_noisy_lidar | A | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| A4_object_missing | A | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| A5_stale_belief | A | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| B1_three_colors | B | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 |  |
| B2_false_belief | B | 0/1 | 0/1 | 0/1 | 0/1 | - | mentions one of ['101'] |
| B3_conflicting_reports | B | 0/1 | 0/1 | 1/1 | 1/1 | 1/1 | mentions one of ['green'] |
| H1_unknown_object | grounding | 0/1 | 0/1 | 0/1 | - | 1/1 | mentions one of ["don't know", 'do not know', 'no record', 'no records', 'no information', 'unknown', 'cannot determine', "can't determine", 'no data', "don't have", 'do not have', 'not able', 'unable'] |
| P1_provenance | provenance | 1/1 | 1/1 | 1/1 | - | - |  |
