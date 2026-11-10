---
name: invoice-total
description: Compute an invoice grand total using the house tax and early-payment discount rules.
tags: [billing, invoice, tax, discount, money]
version: 1.0.0
entrypoint: scripts/run.py
---

# invoice-total

## Procedure
1. Sum line items. Each line is {"kind": "goods"|"service", "qty": n, "unit": price}.
2. Apply sales tax of 8.25% to goods lines only. Service lines are tax exempt.
3. If `days_to_pay` <= 10, subtract a 2% early-payment discount from the taxed total.
4. Round half-up to cents once, at the end. Do not round per line.
Output: {"total": "<decimal string with 2 places>"}.

## Run
`python scripts/run.py < input.json` prints the output JSON.
