---
name: customer-dedupe
description: Deduplicate customer records by canonical email, keeping the most recently updated row.
tags: [crm, customers, dedupe, email, data cleaning]
version: 1.0.0
entrypoint: scripts/run.py
---

# customer-dedupe

## Procedure
1. Canonical email: lowercase. For gmail.com and googlemail.com: drop dots in the local part,
   drop anything after `+`, and map the domain to gmail.com.
2. Other domains: lowercase only (dots and `+tags` are significant).
3. For each canonical email keep the row with the latest `updated_at` (ISO date string).
Output: {"ids": [kept ids sorted ascending]}.

## Run
`python scripts/run.py < input.json` prints the output JSON.
