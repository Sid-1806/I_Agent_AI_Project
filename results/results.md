# I, Agent: evaluation results

Correct answer = every answer check passed (the fair comparison across levels).
All checks = answer, tools, memory and grounding checks all passed.

| System | Set | Level | Model | Temp | Runs | Correct answer | All checks | Errors |
|---|---|---|---|---|---|---|---|---|
| v1 | dev | baseline | qwen2.5:7b | 0 | 20 | 10/20 (50%, 95% CI 30–70%) | 0/20 (0%, 95% CI 0–16%) | 0 |
| v1 | dev | sensors | qwen2.5:7b | 0 | 10 | 7/10 (70%, 95% CI 40–89%) | 1/10 (10%, 95% CI 2–40%) | 0 |
| v1 | dev | plain | qwen2.5:7b | 0 | 10 | 5/10 (50%, 95% CI 24–76%) | 2/10 (20%, 95% CI 6–51%) | 0 |
| v1 | dev | checks | qwen2.5:7b | 0 | 10 | 8/10 (80%, 95% CI 49–94%) | 4/10 (40%, 95% CI 17–69%) | 0 |
| v1 | dev | full | qwen2.5:7b | 0 | 60 | 49/60 (82%, 95% CI 70–89%) | 48/60 (80%, 95% CI 68–88%) | 0 |
| v1 | heldout | baseline | qwen2.5:7b | 0 | 10 | 4/10 (40%, 95% CI 17–69%) | 0/10 (0%, 95% CI 0–28%) | 0 |
| v1 | heldout | sensors | qwen2.5:7b | 0 | 10 | 5/10 (50%, 95% CI 24–76%) | 0/10 (0%, 95% CI 0–28%) | 0 |
| v1 | heldout | plain | qwen2.5:7b | 0 | 10 | 7/10 (70%, 95% CI 40–89%) | 3/10 (30%, 95% CI 11–60%) | 0 |
| v1 | heldout | full | qwen2.5:7b | 0 | 29 | 22/29 (76%, 95% CI 58–88%) | 18/29 (62%, 95% CI 44–77%) | 0 |
| v1 | heldout | full | qwen2.5:7b | 0.7 | 12 | 10/12 (83%, 95% CI 55–95%) | 9/12 (75%, 95% CI 47–91%) | 0 |
| v2 | dev | full | qwen2.5:7b | 0 | 13 | 11/13 (85%, 95% CI 58–96%) | 10/13 (77%, 95% CI 50–92%) | 0 |

## Correct answers per scenario (qwen2.5:7b, temperature 0)

| Set | Scenario | baseline v1 | sensors v1 | plain v1 | checks v1 | full v1 | full v2 |
|---|---|---|---|---|---|---|---|
| dev | A1_route_blocked | 0/2 | 0/1 | 0/1 | 1/1 | 6/6 | 1/1 |
| dev | A2_route_reopened | 0/2 | 1/1 | 0/1 | 0/1 | 6/6 | 1/1 |
| dev | A3_noisy_lidar | 2/2 | 1/1 | 0/1 | 1/1 | 6/6 | 1/1 |
| dev | A4_object_missing | 2/2 | 0/1 | 1/1 | 1/1 | 6/6 | 1/1 |
| dev | A5_stale_belief | 0/2 | 0/1 | 1/1 | 1/1 | 6/6 | 1/1 |
| dev | A6_scan_before_driving | - | - | - | - | - | 1/1 |
| dev | A7_report_vs_camera | - | - | - | - | - | 0/1 |
| dev | B1_three_colors | 0/2 | 1/1 | 0/1 | 1/1 | 5/6 | 1/1 |
| dev | B2_false_belief | 2/2 | 1/1 | 1/1 | 1/1 | 6/6 | 1/1 |
| dev | B3_conflicting_reports | 2/2 | 1/1 | 1/1 | 1/1 | 0/6 | 1/1 |
| dev | B4_user_insists | - | - | - | - | - | 0/1 |
| dev | H1_unknown_object | 2/2 | 1/1 | 0/1 | 0/1 | 2/6 | 1/1 |
| dev | P1_provenance | 0/2 | 1/1 | 1/1 | 1/1 | 6/6 | 1/1 |
| heldout | HA1_right_route_blocked | 0/1 | 0/1 | 1/1 | - | 3/3 | - |
| heldout | HA2_left_route_reopened | 0/1 | 0/1 | 1/1 | - | 3/3 | - |
| heldout | HA3_noisy_left_scan | 1/1 | 0/1 | 1/1 | - | 3/3 | - |
| heldout | HA4_crate_missing_dim_room | 0/1 | 1/1 | 0/1 | - | 3/3 | - |
| heldout | HA5_crate_found_elsewhere | 0/1 | 0/1 | 1/1 | - | 3/3 | - |
| heldout | HB1_cup_dim_light | 0/1 | 1/1 | 0/1 | - | 0/3 | - |
| heldout | HB2_keys_moved | 1/1 | 1/1 | 0/1 | - | 1/2 | - |
| heldout | HB3_three_robot_reports | 1/1 | 1/1 | 1/1 | - | 2/3 | - |
| heldout | HH1_unknown_weight | 1/1 | 1/1 | 1/1 | - | 1/3 | - |
| heldout | HP1_provenance_reason | 0/1 | 0/1 | 1/1 | - | 3/3 | - |
