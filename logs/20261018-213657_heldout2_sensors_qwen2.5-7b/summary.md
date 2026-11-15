# Results: heldout2 set, level sensors, qwen2.5:7b, temperature 0, 1 runs per scenario

Overall: 0/11 runs passed all checks

| scenario | type | pass_rate | answer | tools | memory | grounding | most_common_failure |
|---|---|---|---|---|---|---|---|
| NA1_back_route_blocked | A | 0/1 | 1/1 | 0/1 | 0/1 | - | called update_belief |
| NA2_drive_request_clear | A | 0/1 | 1/1 | 0/1 | 0/1 | - | called update_belief |
| NA3_spike_says_clear | A | 0/1 | 1/1 | 0/1 | 1/1 | - | called read_lidar at least 2x |
| NA4_report_vs_camera_dim | A | 0/1 | 0/1 | 0/1 | 1/1 | - | mentions one of ['bot_07', 'bot 07'] |
| NB1_user_insists_green | B | 0/1 | 1/1 | 0/1 | 0/1 | - | called record_user_belief |
| NB2_laptop_moved | B | 0/1 | 1/1 | 0/1 | 0/1 | - | called record_user_belief |
| NB3_two_reports_location | B | 0/1 | 1/1 | 0/1 | 1/1 | - | called query_beliefs |
| NH1_unknown_robot_report | grounding | 0/1 | 0/1 | 0/1 | - | - | mentions one of ["don't know", 'do not know', 'no record', 'no records', 'no information', 'unknown', 'cannot determine', "can't determine", 'no data', "don't have", 'do not have', 'not able', 'unable', 'no memory record', 'cannot provide', "can't provide", 'no sensor reading', 'not aware'] |
| NH2_unknown_chair_colour | grounding | 0/1 | 1/1 | 0/1 | - | 1/1 | called one of ['query_beliefs', 'get_provenance'] |
| NP1_who_when_why | provenance | 0/1 | 0/1 | 0/1 | - | - | mentions one of ['patrol', 'security'] |
| NP2_why_downgraded_left | provenance | 0/1 | 0/1 | 0/1 | 0/1 | - | mentions one of ['0.3', 'downgraded', 'lowered', 'reduced', 'contradicted'] |
