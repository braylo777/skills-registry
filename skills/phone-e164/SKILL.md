---
name: phone-e164
description: Convert human-written phone numbers to E.164, defaulting to the US country code.
tags: [phone, telephone, e164, contacts, format]
version: 1.0.0
entrypoint: scripts/run.py
---

# phone-e164

## Procedure
1. Keep a leading `+`; strip every other non-digit.
2. No `+`: 10 digits -> prefix +1. 11 digits starting with 1 -> prefix +.
3. A leading `00` is an international prefix: replace with `+`.
4. Anything else is invalid -> null.
Output: {"numbers": ["+...", null, ...]}.

## Run
`python scripts/run.py < input.json` prints the output JSON.
