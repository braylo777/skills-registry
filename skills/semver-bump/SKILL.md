---
name: semver-bump
description: Decide the next semantic version from conventional commit messages, including the pre-1.0 rule.
tags: [release, version, semver, commits, changelog]
version: 1.0.0
entrypoint: scripts/run.py
---

# semver-bump

## Procedure
1. Read the current version and the list of commit subjects/bodies.
2. `BREAKING CHANGE` in a body or `!` after the type (e.g. `feat!:`) is a breaking change.
3. Breaking -> major bump. But if major is 0, a breaking change bumps MINOR (pre-1.0 rule).
4. Else any `feat` -> minor. Else any `fix` or `perf` -> patch. Else no release.
5. A bump resets lower fields to 0.
Output: {"next": "X.Y.Z"} or {"next": null}.

## Run
`python scripts/run.py < input.json` prints the output JSON.
