# Results: dev set, level full, qwen2.5:7b, temperature 0, 1 runs per scenario (rescored 2026-11-15 22:19)

Overall: 15/15 runs passed all checks

| scenario | type | pass_rate | answer | tools | memory | grounding | most_common_failure |
|---|---|---|---|---|---|---|---|
| A1_route_blocked | A | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| A2_route_reopened | A | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| A3_noisy_lidar | A | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| A4_object_missing | A | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| A5_stale_belief | A | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| B1_three_colors | B | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 |  |
| B2_false_belief | B | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| B3_conflicting_reports | B | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 |  |
| H1_unknown_object | grounding | 1/1 | 1/1 | 1/1 | - | 1/1 |  |
| P1_provenance | provenance | 1/1 | 1/1 | 1/1 | - | - |  |
| A6_scan_before_driving | A | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| A7_report_vs_camera | A | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| B4_user_insists | B | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| H2_unknown_room | grounding | 1/1 | 1/1 | 1/1 | - | - |  |
| P2_why_downgraded | provenance | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
