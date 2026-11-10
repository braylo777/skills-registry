---
name: incident-severity
description: Assign an incident priority P1, P2 or P3 to an alert using the on-call severity matrix.
tags: [ops, incident, on-call, severity, alerting]
version: 1.0.0
entrypoint: scripts/run.py
---

# incident-severity

## Procedure
1. P1 if any: `error_rate` >= 0.05, `customer_facing` and `region_down`, or text contains `data loss`.
2. P2 if any: `error_rate` >= 0.01, `p95_ms` >= 2000, or text contains `OOM` or `disk full`.
3. Otherwise P3.
4. Business hours do not change priority.
Output: {"priority": "P1"|"P2"|"P3"}.

## Run
`python scripts/run.py < input.json` prints the output JSON.
