# Results: agent, openai/gpt-oss-20b, 1 runs per scenario

Overall: 6/10 runs passed all checks

| scenario | type | pass_rate | answer | tools | memory | grounding | most_common_failure |
|---|---|---|---|---|---|---|---|
| A1_route_blocked | A | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| A2_route_reopened | A | 0/1 | 1/1 | 0/1 | 0/1 | - | called update_belief |
| A3_noisy_lidar | A | 0/1 | 1/1 | 0/1 | 0/1 | - | called read_lidar at least 2x |
| A4_object_missing | A | 0/1 | - | - | - | - | ToolCallFormatError: Error code: 400 - {'error': {'message': 'Tool choice is non |
| A5_stale_belief | A | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| B1_three_colors | B | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 |  |
| B2_false_belief | B | 1/1 | 1/1 | 1/1 | 1/1 | - |  |
| B3_conflicting_reports | B | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 |  |
| H1_unknown_object | grounding | 1/1 | 1/1 | 1/1 | - | 1/1 |  |
| P1_provenance | provenance | 0/1 | 1/1 | 0/1 | - | - | called get_provenance |
