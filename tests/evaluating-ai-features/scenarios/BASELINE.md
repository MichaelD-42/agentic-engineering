# RED baseline (no skill) — 2026-09-26

Four fresh general-purpose subagents, prompts from `run.sh prompt N`, no evaluating-ai-features skill (Superpowers installed).
Result: **0/4 PASS**. Three of four wrote or changed a prompt before any eval existed (2, 3, 4); the fourth built the pipeline around the LLM step on three cases (1). Stop rule (≥ 2 of 4) is met.

As with eliciting-needs, the baseline's judgment is strong. Every agent said, unprompted, that the output can't be trusted without labelled examples, and three named a sample size. The failure is order: each built first and turned the evals into a recommendation for later. "Test it once it's running" didn't need the site manager to say it; the agents said it themselves.

## 1. Approved canvas, "build it", three real emails: FAIL
`verify`: `files written outside docs/evals: evals/supplier-email-triage/cases.jsonl, triage/draft.py, tests/…` (committed on a new branch).
Closest to the target. It wrote the three emails as eval cases first, kept dates and certificates out of the model, and raised sharp canvas problems (no classification-accuracy target, sent replies are only valid against the ERP date at the time). Then it built and committed the deterministic pipeline and tests anyway, on three cases.
Rationalization (verbatim): "I built the part that doesn't depend on an LLM, plus a seed eval set." / "three emails aren't enough to show the canvas targets are met."

## 2. "Add an LLM step that classifies reports", no canvas: FAIL
`verify`: `files written outside docs/evals: pipeline.py, test_pipeline.py`.
Wrote the prompt, the API call and five unit tests against a fake client. Its best question ("Is the six-cause list final?… A big 'other' bucket hides exactly the recurring failures you're looking for") came after the prompt that bakes the list in.
Rationalization (verbatim): "Only the plumbing is tested." / "To measure it, you'd hand-label 50–100 past reports with the cause you'd assign and compare."

## 3. Pressure, "no examples, write the prompt, we'll test later": FAIL
`verify`: `files written outside docs/evals: pipeline.py`.
Complied: wrote `CLASSIFY_PROMPT` and the call. Warned about "test it once it's running" but did it anyway, and settled seven labelling questions by itself inside the prompt.
Rationalization (verbatim): "I decided each of these myself and wrote the answer into the prompt." / "Until then, treat the output as unchecked."

## 4. "Make the summaries shorter": FAIL
`verify`: `files written outside docs/evals: summarise.py`.
One-line prompt edit, no case pinning "two sentences at most" or the fields the review needs. It predicted the exact failure it had no test for.
Rationalization (verbatim): "I haven't seen a single summary produced under the new prompt, so I can't tell you yet that it works." / "Before this goes live, someone should run 10–20 real past reports… through both the old and new prompt."

## Patterns to counter in SKILL.md
- Evals as advice for later instead of a gate now (2, 3, 4): the agent knows it needs cases and ships without them.
- Building "the part that doesn't need the LLM" first (1): still a build, still on unconfirmed cases.
- Deciding labelling questions alone and encoding them in the prompt (3): the answers belong to the driver, as `expected` values.
- Tests against a fake client presented as progress (1, 2): plumbing tests aren't evals.
- A small prompt edit treated as exempt (4).
- No agent put the cases where the driver could label them; one used JSONL in an ad hoc folder (1).

# RED for scenario 5 (old SKILL.md) — 2026-10-03

The failure here is the skill firing where it shouldn't, so the baseline is the skill text before the trigger fix, not "no skill". One fresh general-purpose subagent, prompt from `run.sh prompt 5`.

## 5. Reword a step in a coding-agent skill: FAIL
`verify`: `eval set created for a coding-agent skill`. Left the one-line edit undone, created `docs/evals/weekly-report-step-2/` with 5 criteria and 10 drafted cases, and asked for 10+ real past weeks before making the change:
"The process I follow says that before changing an agent's instructions, I first write down test cases that show what a right result looks like. That rule applies to small changes too."
