---
name: code-review
description: Review a diff or pull request for correctness, security, and maintainability before it merges. Use after writing or changing code, and before committing to a shared branch.
version: 1.0.0
license: MIT
author: agentstack (Sasindu Dilshan Ranwadana)
platforms: [linux, macos, windows]
tags: [review, quality, security]
---

# Code Review

A small, repeatable review pass. The goal is to catch the issues that cost the
most — a shipped security hole or data-loss bug — not to relitigate style.

## Process

1. **Read the change, not the file.** `git diff <base>...HEAD`. Review what
   actually changed and the lines around it, not the whole codebase.
2. **Security first.** For any change touching auth, user input, database
   queries, file paths, external calls, or crypto:
   - No hardcoded secrets (keys, tokens, passwords).
   - User input validated at the boundary; queries parameterized.
   - Output encoded where it reaches HTML/shell/SQL.
   - Errors don't leak stack traces or secrets to users.
3. **Correctness.** Does each changed function do what its name claims? Are
   error paths handled, or silently swallowed? Are edge cases (empty, null,
   large, concurrent) covered by a test you can point to?
4. **Maintainability.** Functions focused (<50 lines), files cohesive, no deep
   nesting, no copy-paste drift, names that read without a comment.
5. **Tests.** New behavior has a test that would fail without the change.

## Severity

Report findings graded by what a user gets if it ships, not by how the spec
reads:

| Level | Meaning | Action |
|-------|---------|--------|
| Critical | Security hole or data loss | Block — fix before merge |
| Important | Bug or real quality risk | Fix before merge |
| Minor | Style or polish | Note; author decides |

Lead with the Critical/Important findings and name the file and line for each.
If there are none, say so plainly.
