# Results: agent, qwen2.5:7b, 5 runs per scenario (rescored 2026-10-05 21:44) (rescored 2026-11-15 22:18)

Overall: 39/50 runs passed all checks

| scenario | type | pass_rate | answer | tools | memory | grounding | most_common_failure |
|---|---|---|---|---|---|---|---|
| A1_route_blocked | A | 5/5 | 5/5 | 5/5 | 5/5 | - |  |
| A2_route_reopened | A | 4/5 | 5/5 | 4/5 | 4/5 | - | called update_belief |
| A3_noisy_lidar | A | 5/5 | 5/5 | 5/5 | 5/5 | - |  |
| A4_object_missing | A | 5/5 | 5/5 | 5/5 | 5/5 | - |  |
| A5_stale_belief | A | 5/5 | 5/5 | 5/5 | 5/5 | - |  |
| B1_three_colors | B | 4/5 | 4/5 | 5/5 | 5/5 | 5/5 | mentions one of ['blue'] |
| B2_false_belief | B | 5/5 | 5/5 | 5/5 | 5/5 | - |  |
| B3_conflicting_reports | B | 0/5 | 0/5 | 5/5 | 5/5 | 5/5 | mentions one of ['green'] |
| H1_unknown_object | grounding | 1/5 | 1/5 | 5/5 | - | 5/5 | mentions one of ["don't know", 'do not know', 'no record', 'no records', 'no information', 'unknown', 'cannot determine', "can't determine", 'no data', "don't have", 'do not have', 'not able', 'unable', 'no memory record', 'cannot provide', "can't provide", 'no sensor reading', 'not aware'] |
| P1_provenance | provenance | 5/5 | 5/5 | 5/5 | - | - |  |
