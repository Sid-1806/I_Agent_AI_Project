# I, Agent: evaluation results

Correct answer = every answer check passed (the fair comparison across levels).
All checks = answer, tools, memory and grounding checks all passed.

| Set | Level | Model | Temp | Runs | Correct answer | All checks | Errors |
|---|---|---|---|---|---|---|---|
| dev | baseline | qwen2.5:7b | 0 | 10 | 5/10 (50%, 95% CI 24–76%) | 0/10 (0%, 95% CI 0–28%) | 0 |
| dev | full | qwen2.5:7b | 0 | 60 | 49/60 (82%, 95% CI 70–89%) | 48/60 (80%, 95% CI 68–88%) | 0 |

## Correct answers per scenario (qwen2.5:7b, temperature 0)

| Set | Scenario | baseline | sensors | plain | checks | full |
|---|---|---|---|---|---|---|
| dev | A1_route_blocked | 0/1 | - | - | - | 6/6 |
| dev | A2_route_reopened | 0/1 | - | - | - | 6/6 |
| dev | A3_noisy_lidar | 1/1 | - | - | - | 6/6 |
| dev | A4_object_missing | 1/1 | - | - | - | 6/6 |
| dev | A5_stale_belief | 0/1 | - | - | - | 6/6 |
| dev | B1_three_colors | 0/1 | - | - | - | 5/6 |
| dev | B2_false_belief | 1/1 | - | - | - | 6/6 |
| dev | B3_conflicting_reports | 1/1 | - | - | - | 0/6 |
| dev | H1_unknown_object | 1/1 | - | - | - | 2/6 |
| dev | P1_provenance | 0/1 | - | - | - | 6/6 |
