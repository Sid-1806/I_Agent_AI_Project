# Results: agent, qwen2.5:7b, 1 runs per scenario (rescored 2026-09-26 15:55) (rescored 2026-10-05 21:44)

Overall: 9/10 runs passed all checks

| scenario | type | pass_rate | answer | tools | memory | grounding | most_common_failure |
|---|---|---|---|---|---|---|---|
| A1_route_blocked | A | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| A2_route_reopened | A | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| A3_noisy_lidar | A | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| A4_object_missing | A | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| A5_stale_belief | A | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| B1_three_colors | B | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 |  |
| B2_false_belief | B | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| B3_conflicting_reports | B | 0/1 | 0/1 | 1/1 | 1/1 | 1/1 | mentions one of ['blue'] |
| H1_unknown_object | grounding | 1/1 | 1/1 | 1/1 | - | 1/1 |  |
| P1_provenance | provenance | 1/1 | 1/1 | 1/1 | - | - |  |
