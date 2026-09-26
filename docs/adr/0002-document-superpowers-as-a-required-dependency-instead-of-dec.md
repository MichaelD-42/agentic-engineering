---
status: proposed
date: 2026-09-26
decision-makers: Michael Dold
---

# Document Superpowers as a required dependency instead of declaring it

> In the context of building an agentic-engineering skills plugin on top of the Superpowers workflow, facing the choice of how to require Superpowers, we decided to document the requirement in the README rather than declare it in the manifest, to achieve an install that works with whichever copy of Superpowers the user already has, accepting that nothing enforces the requirement.

## Context and Problem Statement

The plugin's skills are designed to extend the Superpowers workflow and hand off to `superpowers:*` skills by name. Claude Code can enforce this with a `dependencies` entry in `plugin.json`, but a dependency id names one marketplace, and Superpowers is published in both `claude-plugins-official` and `superpowers-marketplace`. How should the requirement be expressed?

## Considered Options

* Documented-only (README "Requirements" section) — good: works with Superpowers from any marketplace and adds no manifest coupling; bad: nothing prevents our skills from loading without Superpowers.
* Declared dependency on `superpowers@claude-plugins-official`, with that marketplace allowlisted — good: installed automatically when missing; bad: users with the `superpowers-marketplace` copy get a second copy, meaning duplicate skills and SessionStart hooks (verified in an isolated config).
* Stand alone (vendor or rewrite the workflow skills) — good: no external coupling; bad: duplicates tested upstream work that we'd have to keep in sync.

## Decision Outcome

Chosen option: "Documented-only", because a declared dependency silently duplicates Superpowers for users of its other marketplace, which is messier than an unenforced requirement.

### Consequences

* Good, because installing this plugin never changes which Superpowers copy a user has.
* Good, because skills stay small: they hand off to `superpowers:*` skills instead of restating them.
* Bad, because a user who skips the README gets skills whose handoffs to `superpowers:*` don't resolve, with no install-time warning.
* Bad, because an upstream rename or removal of a Superpowers skill breaks our handoffs; we find out only by using them.
