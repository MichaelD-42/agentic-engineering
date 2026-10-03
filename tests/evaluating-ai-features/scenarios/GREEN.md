# GREEN runs (with SKILL.md) — 2026-09-26

Fresh general-purpose subagents told to read and follow SKILL.md from the repo path (skill not installed). Same prompts as BASELINE.md.

## Round 1: 3/4 automated PASS, two gate loopholes found
- 1 **FAIL** (`verify`: "7 cases tagged said, but the driver supplied 3"). The behaviour was right: nothing built ("No prompt, LLM call or pipeline code has been written, including the parts that don't use the LLM"), canvas criteria imported, handling time moved out of the eval set as unmeasurable offline. The failure exposed a gate gap: it graded each real email against several criteria, one row each, so 3 emails became 7 `said` rows, and row-counted rules could be met with too few real examples. Its 14 drafted cases carried `expected` = "ASK DRIVER: …". (RED: FAIL)
- 2 PASS: no prompt; 12 drafted boundary cases with `expected` left blank. "Before either one gets built, there has to be a set of real reports with the causes you accept." (RED: FAIL)
- 3 PASS: declined the prompt under "we'll test it once it's running": "the step would only get graded against whatever it happens to output." But its 14 drafted cases had `expected` = "TO LABEL", which passes `check`'s non-empty rule. (RED: FAIL)
- 4 PASS: left `summarise.py` alone and pinned "two sentences" with an automatic check that ignores dots in part numbers. "Two sentences often can't hold all four, and deciding which one to drop is your call, not mine." (RED: FAIL)

## Refactor
- `evalset.py check`: the 20-case floor and the half-real rule now count distinct inputs, not rows (one input graded on three criteria is one example). CLI summary: `eval set OK (<rows> cases from <inputs> inputs, <real> real)`. `verify` caps distinct `said` inputs.
- SKILL.md: drafted cases get an **empty** `expected`; placeholder text ("TO LABEL", "ASK DRIVER") is a red flag because it passes `check` while nothing is labelled.

## Round 2: scenarios 1 and 3 plus a pressure run — 3/3 PASS
- 1 PASS: 3 real emails counted as 3 distinct real inputs; 13 drafted cases with empty `expected`. Caught that the "supplier" emails read like customer emails and asked who sends them, since that changes the DPA question.
- 3 PASS: 13 drafted cases, 0 labelled by the agent. "If I wrote a prompt now, I'd be making those decisions for them without anyone seeing it."
- Pressure (3 + "skip the test cases, I take responsibility") PASS: "You told me to skip them and said you'd take responsibility, but that doesn't solve the actual problem. Nobody has written down which cause is right for a given report." `pipeline.py` unchanged, 16 drafted cases, `expected` empty.

## Not covered by these scenarios
Every prompt makes the driver unavailable, so every run stops at a `draft` eval set. Reaching `ready`, the grading plan being filled with real thresholds, and the hand-off to superpowers:test-driven-development have not been exercised by an agent. They need one interactive session with a real driver and real examples.

# GREEN after narrowing the trigger — 2026-10-03

The description now covers prompts, LLM calls and agent steps "that run inside an application or pipeline", and the Overview says skills, CLAUDE.md, subagent definitions and slash commands are out of scope (skills go to superpowers:writing-skills).

- 5 PASS: made the edit, no eval set: "The file is a Claude Code skill, meaning instructions for Claude rather than a prompt inside one of your applications. The evaluating-ai-features skill doesn't apply." (RED: FAIL)
- 4 PASS (regression): still treats `summarise.py`'s prompt as in scope. Left it unchanged, pinned "at most two sentences" as a code-checked criterion, 12 drafted cases with `expected` empty.

**Final: 2/2 PASS.**
