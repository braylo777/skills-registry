---
name: shipping-weight
description: Work out the billable parcel weight from box dimensions and actual weight with the carrier divisor.
tags: [shipping, parcel, weight, logistics, carrier]
version: 1.0.0
entrypoint: scripts/run.py
---

# shipping-weight

## Procedure
1. Dimensions are inches. Dimensional weight = L * W * H / 139 (pounds).
2. Billable weight = max(actual_lb, dimensional weight).
3. Round billable weight UP to the next whole pound (ceiling). 4.0 stays 4.
Output: {"billable_lb": int}.

## Run
`python scripts/run.py < input.json` prints the output JSON.
