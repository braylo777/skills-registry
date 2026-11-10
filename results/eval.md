| condition | success | mean prompt tokens | correct skill | wrong skill | no skill | distractor false loads |
|---|---|---|---|---|---|---|
| no_skills | 19/40 (0.475) | 74 | 0 | 0 | 40 | 0/8 |
| all_in_context | 40/40 (1.000) | 1591 | 40 | 0 | 0 | 0/8 |
| registry | 33/40 (0.825) | 421 | 29 | 5 | 6 | 3/8 |

| threshold | success | correct | wrong | none | distractor false loads | mean tokens |
|---|---|---|---|---|---|---|
| 0.0 | 0.800 | 32 | 8 | 0 | 8 | 466 |
| 0.05 | 0.850 | 32 | 6 | 2 | 3 | 437 |
| 0.1 | 0.825 | 31 | 6 | 3 | 3 | 433 |
| 0.15 | 0.825 | 29 | 5 | 6 | 3 | 421 |
| 0.2 | 0.850 | 29 | 3 | 8 | 1 | 404 |
| 0.3 | 0.825 | 25 | 2 | 13 | 1 | 385 |
| 0.4 | 0.850 | 24 | 1 | 15 | 0 | 373 |
