---
name: date-normalize
description: Normalize messy date strings to the house YYYY-MM-DD format with the two-digit-year pivot.
tags: [dates, format, iso, parsing, cleanup]
version: 1.0.0
entrypoint: scripts/run.py
---

# date-normalize

## Procedure
1. Accept `MM/DD/YYYY`, `MM/DD/YY`, `D Mon YYYY` (e.g. `3 Nov 2026`) and ISO timestamps.
2. Slash dates are US order: month first.
3. Two-digit years: 00-69 -> 2000-2069, 70-99 -> 1970-1999.
4. ISO timestamps: keep the date part only; do not convert time zones.
Output: {"dates": ["YYYY-MM-DD", ...]} in input order.

## Run
`python scripts/run.py < input.json` prints the output JSON.
