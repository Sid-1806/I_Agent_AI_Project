# I, Agent: evaluation results

Correct answer = every answer check passed (the fair comparison across levels).
All checks = answer, tools, memory and grounding checks all passed.

| System | Set | Level | Model | Temp | Runs | Correct answer | All checks | Errors |
|---|---|---|---|---|---|---|---|---|
| v1 | dev | baseline | qwen2.5:7b | 0 | 20 | 10/20 (50%, 95% CI 30–70%) | 0/20 (0%, 95% CI 0–16%) | 0 |
| v1 | dev | sensors | qwen2.5:7b | 0 | 10 | 8/10 (80%, 95% CI 49–94%) | 1/10 (10%, 95% CI 2–40%) | 0 |
| v1 | dev | plain | qwen2.5:7b | 0 | 10 | 5/10 (50%, 95% CI 24–76%) | 2/10 (20%, 95% CI 6–51%) | 0 |
| v1 | dev | checks | qwen2.5:7b | 0 | 10 | 8/10 (80%, 95% CI 49–94%) | 4/10 (40%, 95% CI 17–69%) | 0 |
| v1 | dev | full | qwen2.5:7b | 0 | 60 | 49/60 (82%, 95% CI 70–89%) | 48/60 (80%, 95% CI 68–88%) | 0 |
| v1 | heldout | baseline | qwen2.5:7b | 0 | 10 | 5/10 (50%, 95% CI 24–76%) | 0/10 (0%, 95% CI 0–28%) | 0 |
| v1 | heldout | sensors | qwen2.5:7b | 0 | 10 | 5/10 (50%, 95% CI 24–76%) | 0/10 (0%, 95% CI 0–28%) | 0 |
| v1 | heldout | plain | qwen2.5:7b | 0 | 10 | 7/10 (70%, 95% CI 40–89%) | 3/10 (30%, 95% CI 11–60%) | 0 |
| v1 | heldout | full | qwen2.5:7b | 0 | 29 | 24/29 (83%, 95% CI 65–92%) | 20/29 (69%, 95% CI 51–83%) | 0 |
| v1 | heldout | full | qwen2.5:7b | 0.7 | 12 | 10/12 (83%, 95% CI 55–95%) | 9/12 (75%, 95% CI 47–91%) | 0 |
| v2 | dev | baseline | qwen2.5:7b | 0 | 15 | 4/15 (27%, 95% CI 11–52%) | 0/15 (0%, 95% CI 0–20%) | 0 |
| v2 | dev | sensors | qwen2.5:7b | 0 | 15 | 14/15 (93%, 95% CI 70–99%) | 1/15 (7%, 95% CI 1–30%) | 0 |
| v2 | dev | full | qwen2.5:7b | 0 | 60 | 60/60 (100%, 95% CI 94–100%) | 59/60 (98%, 95% CI 91–100%) | 0 |
| v2 | heldout | full | qwen2.5:7b | 0 | 10 | 9/10 (90%, 95% CI 60–98%) | 7/10 (70%, 95% CI 40–89%) | 0 |
| v2 | heldout2 | baseline | qwen2.5:7b | 0 | 11 | 5/11 (45%, 95% CI 21–72%) | 0/11 (0%, 95% CI 0–26%) | 0 |
| v2 | heldout2 | sensors | qwen2.5:7b | 0 | 11 | 7/11 (64%, 95% CI 35–85%) | 0/11 (0%, 95% CI 0–26%) | 0 |
| v2 | heldout2 | plain | qwen2.5:7b | 0 | 11 | 8/11 (73%, 95% CI 43–90%) | 3/11 (27%, 95% CI 10–57%) | 0 |
| v2 | heldout2 | checks | qwen2.5:7b | 0 | 11 | 8/11 (73%, 95% CI 43–90%) | 5/11 (45%, 95% CI 21–72%) | 0 |
| v2 | heldout2 | full | qwen2.5:7b | 0 | 33 | 27/33 (82%, 95% CI 66–91%) | 25/33 (76%, 95% CI 59–87%) | 0 |
| v3 | dev | full | qwen2.5:7b-8k | 0 | 13 | 13/13 (100%, 95% CI 77–100%) | 13/13 (100%, 95% CI 77–100%) | 0 |
| v3 | heldout | full | qwen2.5:7b-8k | 0 | 10 | 10/10 (100%, 95% CI 72–100%) | 10/10 (100%, 95% CI 72–100%) | 0 |
| v3 | heldout2 | full | qwen2.5:7b-8k | 0 | 11 | 11/11 (100%, 95% CI 74–100%) | 11/11 (100%, 95% CI 74–100%) | 0 |
| v4 | dev | full | qwen2.5:7b-8k | 0 | 15 | 14/15 (93%, 95% CI 70–99%) | 13/15 (87%, 95% CI 62–96%) | 0 |
| v4 | heldout | full | qwen2.5:7b-8k | 0 | 10 | 10/10 (100%, 95% CI 72–100%) | 9/10 (90%, 95% CI 60–98%) | 0 |
| v4 | heldout2 | full | qwen2.5:7b-8k | 0 | 11 | 11/11 (100%, 95% CI 74–100%) | 11/11 (100%, 95% CI 74–100%) | 0 |
| v4 | heldout3 | full | qwen2.5:7b-8k | 0 | 6 | 5/6 (83%, 95% CI 44–97%) | 5/6 (83%, 95% CI 44–97%) | 0 |
| v4.1 | dev | baseline | qwen2.5:7b-8k | 0 | 15 | 5/15 (33%, 95% CI 15–58%) | 0/15 (0%, 95% CI 0–20%) | 0 |
| v4.1 | dev | full | qwen2.5:7b-8k | 0 | 15 | 15/15 (100%, 95% CI 80–100%) | 15/15 (100%, 95% CI 80–100%) | 0 |
| v4.1 | heldout | baseline | qwen2.5:7b-8k | 0 | 10 | 5/10 (50%, 95% CI 24–76%) | 0/10 (0%, 95% CI 0–28%) | 0 |
| v4.1 | heldout | full | qwen2.5:7b-8k | 0 | 10 | 10/10 (100%, 95% CI 72–100%) | 10/10 (100%, 95% CI 72–100%) | 0 |
| v4.1 | heldout2 | baseline | qwen2.5:7b-8k | 0 | 11 | 5/11 (45%, 95% CI 21–72%) | 0/11 (0%, 95% CI 0–26%) | 0 |
| v4.1 | heldout2 | full | qwen2.5:7b-8k | 0 | 11 | 11/11 (100%, 95% CI 74–100%) | 11/11 (100%, 95% CI 74–100%) | 0 |
| v4.1 | heldout3 | baseline | qwen2.5:7b-8k | 0 | 10 | 3/10 (30%, 95% CI 11–60%) | 0/10 (0%, 95% CI 0–28%) | 0 |
| v4.1 | heldout3 | full | qwen2.5:7b-8k | 0 | 10 | 10/10 (100%, 95% CI 72–100%) | 10/10 (100%, 95% CI 72–100%) | 0 |

## Correct answers per scenario (qwen2.5:7b, temperature 0)

| Set | Scenario | baseline v1 | sensors v1 | plain v1 | checks v1 | full v1 | baseline v2 | sensors v2 | plain v2 | checks v2 | full v2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| dev | A1_route_blocked | 2/2 | 0/1 | 0/1 | 1/1 | 6/6 | 1/1 | 0/1 | - | - | 4/4 |
| dev | A2_route_reopened | 0/2 | 1/1 | 0/1 | 0/1 | 6/6 | 0/1 | 1/1 | - | - | 4/4 |
| dev | A3_noisy_lidar | 2/2 | 1/1 | 0/1 | 1/1 | 6/6 | 1/1 | 1/1 | - | - | 4/4 |
| dev | A4_object_missing | 2/2 | 0/1 | 1/1 | 1/1 | 6/6 | 0/1 | 1/1 | - | - | 4/4 |
| dev | A5_stale_belief | 0/2 | 1/1 | 1/1 | 1/1 | 6/6 | 0/1 | 1/1 | - | - | 4/4 |
| dev | A6_scan_before_driving | - | - | - | - | - | 0/1 | 1/1 | - | - | 4/4 |
| dev | A7_report_vs_camera | - | - | - | - | - | 0/1 | 1/1 | - | - | 4/4 |
| dev | B1_three_colors | 0/2 | 1/1 | 0/1 | 1/1 | 5/6 | 0/1 | 1/1 | - | - | 4/4 |
| dev | B2_false_belief | 2/2 | 1/1 | 1/1 | 1/1 | 6/6 | 1/1 | 1/1 | - | - | 4/4 |
| dev | B3_conflicting_reports | 2/2 | 1/1 | 1/1 | 1/1 | 0/6 | 1/1 | 1/1 | - | - | 4/4 |
| dev | B4_user_insists | - | - | - | - | - | 0/1 | 1/1 | - | - | 4/4 |
| dev | H1_unknown_object | 0/2 | 1/1 | 0/1 | 0/1 | 2/6 | 0/1 | 1/1 | - | - | 4/4 |
| dev | H2_unknown_room | - | - | - | - | - | 0/1 | 1/1 | - | - | 4/4 |
| dev | P1_provenance | 0/2 | 1/1 | 1/1 | 1/1 | 6/6 | 0/1 | 1/1 | - | - | 4/4 |
| dev | P2_why_downgraded | - | - | - | - | - | 0/1 | 1/1 | - | - | 4/4 |
| heldout | HA1_right_route_blocked | 1/1 | 0/1 | 1/1 | - | 3/3 | - | - | - | - | 1/1 |
| heldout | HA2_left_route_reopened | 0/1 | 0/1 | 1/1 | - | 3/3 | - | - | - | - | 1/1 |
| heldout | HA3_noisy_left_scan | 1/1 | 0/1 | 1/1 | - | 3/3 | - | - | - | - | 1/1 |
| heldout | HA4_crate_missing_dim_room | 0/1 | 1/1 | 0/1 | - | 3/3 | - | - | - | - | 1/1 |
| heldout | HA5_crate_found_elsewhere | 0/1 | 0/1 | 1/1 | - | 3/3 | - | - | - | - | 1/1 |
| heldout | HB1_cup_dim_light | 0/1 | 1/1 | 0/1 | - | 0/3 | - | - | - | - | 1/1 |
| heldout | HB2_keys_moved | 1/1 | 1/1 | 0/1 | - | 1/2 | - | - | - | - | 1/1 |
| heldout | HB3_three_robot_reports | 1/1 | 1/1 | 1/1 | - | 2/3 | - | - | - | - | 1/1 |
| heldout | HH1_unknown_weight | 1/1 | 1/1 | 1/1 | - | 3/3 | - | - | - | - | 1/1 |
| heldout | HP1_provenance_reason | 0/1 | 0/1 | 1/1 | - | 3/3 | - | - | - | - | 0/1 |
| heldout2 | NA1_back_route_blocked | - | - | - | - | - | 0/1 | 1/1 | 1/1 | 1/1 | 3/3 |
| heldout2 | NA2_drive_request_clear | - | - | - | - | - | 0/1 | 1/1 | 1/1 | 1/1 | 3/3 |
| heldout2 | NA3_spike_says_clear | - | - | - | - | - | 1/1 | 1/1 | 1/1 | 1/1 | 3/3 |
| heldout2 | NA4_report_vs_camera_dim | - | - | - | - | - | 0/1 | 0/1 | 0/1 | 0/1 | 0/3 |
| heldout2 | NB1_user_insists_green | - | - | - | - | - | 1/1 | 1/1 | 0/1 | 0/1 | 3/3 |
| heldout2 | NB2_laptop_moved | - | - | - | - | - | 1/1 | 1/1 | 1/1 | 1/1 | 3/3 |
| heldout2 | NB3_two_reports_location | - | - | - | - | - | 1/1 | 1/1 | 1/1 | 1/1 | 3/3 |
| heldout2 | NH1_unknown_robot_report | - | - | - | - | - | 0/1 | 0/1 | 1/1 | 1/1 | 3/3 |
| heldout2 | NH2_unknown_chair_colour | - | - | - | - | - | 1/1 | 1/1 | 1/1 | 0/1 | 3/3 |
| heldout2 | NP1_who_when_why | - | - | - | - | - | 0/1 | 0/1 | 1/1 | 1/1 | 0/3 |
| heldout2 | NP2_why_downgraded_left | - | - | - | - | - | 0/1 | 0/1 | 0/1 | 1/1 | 3/3 |
