---
name: diagnosing-bugs
description: Find the root cause of a bug before changing code, using a reproduce-hypothesize-test loop instead of guessing. Use when something is broken, flaky, or behaves differently than expected.
version: 1.0.0
license: MIT
author: agentstack (Sasindu Dilshan Ranwadana)
platforms: [linux, macos, windows]
tags: [debugging, diagnosis, root-cause]
---

# Diagnosing Bugs

Guessing at fixes and checking whether the symptom went away is how one bug
becomes three. Find the cause first; the fix is usually small once you have it.

## Loop

1. **Reproduce it reliably.** The smallest input that triggers the bug, every
   time. If you can't reproduce it, you can't confirm you fixed it — spend your
   effort here first.
2. **Capture the evidence.** The exact error, the stack trace, the inputs, the
   environment. Read the whole message, not the first line.
3. **Form one hypothesis.** A specific, falsifiable claim: "the timeout fires
   because the connection is never closed on the error path." Not "something is
   wrong with connections."
4. **Test the hypothesis cheaply.** A log line, a breakpoint, a one-line probe —
   the smallest thing that confirms or kills it. Read the result; don't assume.
5. **Narrow or pivot.** Confirmed → narrow to the exact line. Killed → new
   hypothesis from what the test taught you. Repeat.

## When you have the cause

- Write a failing test that reproduces the bug (RED). This is proof the bug is
  real and, later, proof it's gone.
- Make the smallest change that fixes the cause — not the symptom (GREEN).
- Run the whole suite. A fix that breaks something else isn't done.

## Red flags you're guessing

- You changed more than one thing between tests.
- You can't say which line caused the bug, only which change made the symptom
  disappear.
- You're adding `try/except` to hide an error instead of handling its cause.
