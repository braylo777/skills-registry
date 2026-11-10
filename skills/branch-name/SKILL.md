---
name: branch-name
description: Build a git branch name from a ticket id, change type and summary using the team naming convention.
tags: [git, branch, naming, ticket, slug]
version: 1.0.0
entrypoint: scripts/run.py
---

# branch-name

## Procedure
1. Format: `<type>/<TICKET>-<slug>`. Type is one of feat, fix, chore, docs.
2. TICKET keeps its case, e.g. `PAY-142`.
3. Slug: lowercase, ASCII only (drop accents), words joined by `-`, no stop words (a, an, the, of, for, to, and).
4. Truncate the slug to 30 characters at a word boundary.
Output: {"branch": "..."}.

## Run
`python scripts/run.py < input.json` prints the output JSON.
