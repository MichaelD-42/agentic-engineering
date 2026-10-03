---
status: proposed
date: 2026-10-03
decision-makers: Michael
---

# Enforce ADR metadata with adr.py, not body immutability with hooks

> In the context of the recording-decisions skill, facing a guard on decided ADR bodies that blocked honest fixes yet was easy to bypass, we decided to enforce only ADR metadata (status, dates, supersede links, index) through adr.py and drop the immutability guard, to keep ADRs cheap to maintain, accepting that a change to what was decided is caught only by review, not by tooling.

## Context and Problem Statement

A PreToolUse hook and a HEAD comparison in `adr.py check` blocked any change to the body of a decided ADR, including typo fixes. The guard covered only the Edit and Write tools, so a shell edit bypassed it. Once committed, the change passed `adr.py check`, so CI did not enforce it either. No baseline scenario showed an agent rewriting an accepted decision. The metadata (status, supersede links, index) is what drifts in practice.

## Considered Options

* Enforce metadata only — good: no friction on wording fixes, and the index repairs itself; bad: an in-place change to the decision is caught only in review.
* Keep and harden the guard (compare against the merge base in CI, cover shell edits) — good: decisions are tamper-proof; bad: more tooling, and still more friction on every typo fix.

## Decision Outcome

Chosen option: "Enforce metadata only", because the cost of the guard fell on every edit while the failure it guarded against was never observed.

### Consequences

* Good, because typo and link fixes no longer need a supersede, and the PostToolUse hook regenerates the index instead of failing.
* Good, because every status change now has an `adr.py` command (`accept`, `reject`, `deprecate`, `supersede`), so nothing is written by hand.
* Bad, because "change what was decided only by superseding" is now a convention backed by the skill text and review, not by a check.
