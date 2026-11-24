# Results: heldout3 set, level baseline, qwen2.5:7b-8k, temperature 0, 1 runs per scenario

Overall: 0/10 runs passed all checks

| scenario | type | pass_rate | answer | tools | memory | grounding | most_common_failure |
|---|---|---|---|---|---|---|---|
| IX1_left_passage_blocked | A | 0/1 | 0/1 | 0/1 | 0/1 | - | mentions one of ['blocked', 'obstacle', 'obstructed', 'not passable', 'impassable', 'not clear', "isn't clear", 'is not clear'] |
| IX2_noisy_rear_scan | A | 0/1 | 1/1 | 0/1 | - | - | called read_lidar |
| IX3_keys_on_camera | A | 0/1 | 0/1 | 0/1 | 0/1 | - | mentions one of ['Room_604', 'this room', 'here', 'with me', 'in front of me', 'near me'] |
| IX4_construction_lifted | A | 0/1 | 1/1 | 0/1 | - | - | called read_lidar |
| IX5_user_misplaced_crate | B | 0/1 | 0/1 | 0/1 | 0/1 | - | mentions one of ['no', 'not', "isn't", 'is not', 'incorrect', 'wrong', 'mistaken', 'moved'] |
| IX6_yellow_light_box | B | 0/1 | 0/1 | 0/1 | - | - | mentions one of ['lighting', 'light', 'lights', 'lit', 'illumination'] |
| IX7_robots_disagree_front | B | 0/1 | 1/1 | 0/1 | 0/1 | - | called read_lidar |
| IX8_distant_passage_unknown | grounding | 0/1 | 0/1 | 0/1 | - | - | mentions one of ["don't know", 'do not know', 'not sure', 'no information', 'unknown', 'cannot tell', "can't tell", 'cannot confirm', "can't confirm", 'no data', 'unable', 'not able', 'no record', 'no records', "can't say", 'cannot say'] |
| IX9_unseen_laptop_colour | grounding | 0/1 | 0/1 | - | - | 1/1 | mentions one of ["don't know", 'do not know', 'not sure', 'no information', 'unknown', 'cannot tell', "can't tell", 'cannot confirm', "can't confirm", 'no data', 'unable', 'not able', 'no record', 'no records', "can't say", 'cannot say'] |
| IX10_crate_move_record | provenance | 0/1 | 0/1 | 0/1 | - | - | mentions one of ['2 hours', 'two hours', '7200', '7200 seconds', '120 minutes', '2 h', '2h'] |
