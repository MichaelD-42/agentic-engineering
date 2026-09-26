---
name: evaluating-ai-features
description: Use when about to write or change a prompt, an LLM call or an agent step, or when eliciting-needs hands off a canvas in automate, augment or agent mode
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/evalset.py *)
---

# Evaluating AI Features

## Overview

A prompt without an eval set is code without a test: it works on the three inputs you tried. This skill builds the eval set first, with real examples from the person who knows the right answers, and gates the build on it.

**Core principle:** Know how you'll tell right from wrong before you write the prompt.

The driver is often an engineer, but not a software engineer. Use plain language. Explain any software term in one line the first time you use it.

**Announce at start:** "I'm using the evaluating-ai-features skill to build the test cases before any prompt."

## The Iron Law

```
NO PROMPT UNTIL THE EVAL SET PASSES CHECK
```

Until `evalset.py status <dir> ready` succeeds:
- write nothing outside `docs/evals/`: no prompt, no LLM call, no pipeline around it, no harness code, no "draft to show them";
- put no prompt text in your reply.

This holds for "just a small tweak". It holds when the driver says they'll test later. It holds for "the part that doesn't need the LLM". It holds when you're sure the prompt is obvious.

## Checklist

1. **Start:** `python3 ${CLAUDE_SKILL_DIR}/scripts/evalset.py new "<title>"`, adding `--canvas <path>` when a need canvas exists. Without a canvas, ask one question at a time: what does a right output look like, and what does a wrong one cost? Write the answers as criteria in `plan.md`.
2. **Real cases:** ask the driver for real inputs with the answer they accept (exported emails with the reply sent, past reports with the cause found). Enter each in `cases.csv` as `source` `said`. The CSV opens in Excel, so the driver can add and label rows there.
3. **Fill gaps:** draft `assumed` cases only where criteria, edge cases or refusal inputs are uncovered. Leave their `expected` **empty** for the driver to fill; no placeholder text like "TO LABEL" or "ask driver", because `check` only catches an empty cell. A case the driver confirms becomes `said`. Never label a case yourself and tag it `said`. Open labelling questions ("is a spindle bearing 'bearing' or 'spindle'?") go to the driver as cases to label, not into a prompt as your decision.
4. **Grading plan:** per criterion, a code grader where the output can be checked mechanically, a model rubric otherwise; set k and thresholds from the error tolerance. See `references/graders.md`.
5. **Gate:** `evalset.py status <dir> ready`. Its exit code is the gate; fix the eval set, don't argue with it.
6. **Hand off:** invoke superpowers:test-driven-development. The cases become tests in the project's own stack; they fail until the LLM step exists.

**When the driver can't supply cases now:** fill what you can, keep the set `draft`, and end with the directory path and what's missing, most important first. Build nothing, including the non-LLM parts. "Before this goes live, someone should test it" is the outcome this skill exists to prevent; the eval set is the next step, not a recommendation.

**When changing an existing prompt:** the eval set must exist and pass before the change. If there is none, run this skill first. Add cases that pin the intended change ("two sentences at most") and the behaviour it must not break, before you edit the prompt.

## Red Flags — STOP

- Writing or pasting prompt text before `status ready`
- Building "the part that doesn't depend on the LLM" first
- Unit tests against a fake client presented as progress: they test plumbing, not answers
- "Before this goes live, someone should run real examples": a recommendation instead of the gate
- Deciding labelling questions yourself and writing the answers into the prompt
- Tagging your own examples `said`, or writing `expected` for the driver
- Placeholder text in `expected` ("TO LABEL", "ASK DRIVER: …"): it passes `check` while nothing is labelled
- Cases in an ad hoc file or format instead of `docs/evals/<name>/cases.csv`
- No `refuse` case because "it won't get weird input"
- Editing an existing prompt with no eval set, because the change is small

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "We'll test it once it's running" | Then you'll grade it against what it happens to do. Write down what right means first. |
| "I built the part that doesn't depend on an LLM, plus a seed eval set" | Three cases don't confirm the design. The pipeline waits for the gate like the prompt does. |
| "Only the plumbing is tested" | Then nothing is tested that matters. Plumbing tests come after the eval set, in the TDD hand-off. |
| "I decided each of these myself and wrote the answer into the prompt" | Those were the driver's decisions. Put them in `cases.csv` as cases for the driver to label. |
| "Treat the output as unchecked until someone labels examples" | Unchecked output gets used. Label first, build second. |
| "They have no examples, so I'll generate them" | Generated cases test your idea of the task, not theirs. Draft them `assumed`, and ask the driver to label them. |
| "It's just a small prompt tweak" | Small tweaks break unseen cases. Pin the change with cases, then edit. |
| "A draft prompt helps them picture it" | It anchors everyone on your guess. Show them cases instead. |
| "20 cases is overkill for this" | 20 is the floor for telling a working step from a lucky one. |
| "The check is just a formality" | The check is the gate. Fix the eval set; don't route around it. |
