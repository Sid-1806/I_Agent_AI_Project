# Results: dev set, level full, qwen2.5:7b, temperature 0, 1 runs per scenario

Overall: 10/15 runs passed all checks

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
| A6_scan_before_driving | A | 0/1 | 1/1 | 0/1 | 1/1 | - | did not call move |
| A7_report_vs_camera | A | 0/1 | 0/1 | 1/1 | 1/1 | - | mentions one of ['not here', 'not in this room', 'not in room', 'not present', 'cannot see', "can't see", "don't see", 'do not see', 'not visible', 'not detect', 'did not detect', "didn't detect", "isn't here", 'is not here', 'is not in', "isn't in", 'not currently in', 'not found'] |
| B4_user_insists | B | 0/1 | 0/1 | 1/1 | 1/1 | - | mentions one of ['red'] |
| H2_unknown_room | grounding | 0/1 | 0/1 | 1/1 | - | - | mentions one of ["don't know", 'do not know', 'no record', 'no records', 'no information', 'unknown', 'cannot determine', "can't determine", 'no data', "don't have", 'do not have', 'not able', 'unable', 'no memory record', 'cannot provide', "can't provide", 'no sensor reading', 'not aware', 'cannot see', "can't see"] |
| P2_why_downgraded | provenance | 0/1 | 1/1 | 0/1 | 1/1 | - | called get_provenance |
