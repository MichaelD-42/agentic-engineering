# evaluating-ai-features — design

Date: 2026-09-26
Status: approved in brainstorming, pending spec review

## Goal

Make the eval set come before the prompt, the way the failing test comes before the code. When an agent is about to write or change an LLM step, it first builds a set of labelled cases with the driver, a grading plan tied to the success criteria, and passes a script gate. Only then does the build start, with the cases as the failing tests.

Done means: in the baseline scenarios an agent writes a prompt before any evals; with the skill it doesn't, and it ends with a `ready` eval set or a `draft` one plus a list of what the driver still has to supply.

## Prior art

- `affaan-m/ECC` `eval-harness`: evaluates Claude Code sessions (capability and regression evals, pass@k). Borrowed: the code-grader vs model-grader split and pass@k. Not ported: it targets agent sessions, not an LLM step in a product.
- `eval-driven-dev` (in `majiayu000/claude-skill-registry`): full eval cycle for Python LLM apps, built on the pixie library and a trace DB, starting from existing code. Not ported: framework-bound and code-first.

Neither turns a need into labelled cases before any prompt exists, framework-agnostic, with a non-software engineer supplying the examples.

## Decisions

- **Fires on any new or changed LLM step**, with or without a canvas. With a canvas, it imports the success criteria. Without one, it asks two questions: what a right output looks like, and what a wrong one costs.
- **Produces an eval set and a grading plan; no runner.** `superpowers:test-driven-development` turns the cases into tests in the project's own stack, where CI runs them.
- **A script gate with a floor**, like `canvas.py status` and `adr.py check`: the model can't argue with an exit code.
- **CSV for cases**, so drivers can open and label them in Excel.
- Stdlib Python 3.12 and templates, like the rest of the plugin.
- No ADR: format and thresholds are cheap to change, nothing outside the skill conforms to them.

## Layout

```
skills/evaluating-ai-features/
  SKILL.md
  scripts/evalset.py
  templates/plan.md
  templates/cases.csv
  references/graders.md
docs/evals/<slug>/          created in the user's project by evalset.py new
  plan.md
  cases.csv
```

## Eval set format

`plan.md`:

```markdown
---
name: <title>
status: draft
canvas: <path or empty>
k: 3
---

## Criteria

| id | criterion | grader | threshold |
|---|---|---|---|
| c1 | <from canvas Success criteria, or from the driver> | code \| model | <e.g. ≥ 95% of cases pass all k runs> |

## Grading notes

<per criterion: for code graders the check (exact, schema, regex, numeric tolerance); for model graders the rubric>
```

`cases.csv`, header `id,criterion,source,kind,input,expected,grader`:

- `criterion`: a criterion id from `plan.md`.
- `source`: `said` (a real example the driver supplied or confirmed) or `assumed` (drafted by the agent).
- `kind`: `normal`, `edge`, or `refuse` (an input the step must decline or flag).
- `expected`: the exact output for code-graded cases, or the rubric for model-graded ones.
- `grader`: `code` or `model`.

## `evalset.py`

Same shape as `canvas.py`: argparse subcommands, `--root` (default: cwd), `--today`.

- `new "<title>" [--canvas <path>]` → creates `docs/evals/<slug>/` with `plan.md` and `cases.csv` from the templates. With `--canvas`, every row of the canvas's Success criteria table becomes a criterion (`Metric: Baseline → Target`), ids `c1…cn`. Refuses to overwrite an existing directory. Prints the directory.
- `check <dir>` → prints each problem and exits 1, or prints `eval set OK (<n> cases, <s> said)` and exits 0. Rules:
  1. `plan.md` has front matter with `name`, `status` in `draft|ready`, integer `k ≥ 1`; at least one criterion; every criterion has a grader in `code|model` and a non-empty threshold.
  2. `cases.csv` has exactly the header above; ids are unique; every row's `criterion` exists in `plan.md`; `source`, `kind`, `grader` take only their allowed values; `input` and `expected` are non-empty.
  3. Every criterion has at least one case.
  4. At least 20 cases.
  5. At least half the cases are `said`.
  6. At least one `refuse` case.
- `status <dir> ready|draft` → `ready` only if `check` passes (prints its problems and exits 1 otherwise); `draft` always. Rewrites only the `status` line.

## SKILL.md

Frontmatter: `name: evaluating-ai-features`; `description: Use when about to write or change a prompt, an LLM call or an agent step, or when eliciting-needs hands off a canvas in automate, augment or agent mode`; `allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/evalset.py *)`.

**Iron law:** `NO PROMPT UNTIL THE EVAL SET PASSES CHECK`. Until `evalset.py status <dir> ready` succeeds: nothing written outside `docs/evals/`: no prompt, no LLM call, no harness code.

**Checklist:**

1. `evalset.py new` (with `--canvas` when one exists). No canvas: ask what a right output looks like and what a wrong one costs, one question at a time, and write the answers as criteria.
2. Ask the driver for real cases (exported emails, past reports, historical inputs with known outcomes); enter them as `said`.
3. Draft `assumed` cases only to fill gaps: uncovered criteria, edge cases, refusal inputs. The driver labels their `expected`; the agent never does. A driver-confirmed assumed case becomes `said`.
4. Grading plan: a code grader wherever the output can be checked mechanically; a model rubric otherwise. k and thresholds follow from the error tolerance (`references/graders.md`).
5. `evalset.py status <dir> ready`. Its exit code is the gate.
6. Hand off to `superpowers:test-driven-development`: the cases become tests in the project's stack, and they fail until the LLM step exists.

**Driver can't supply cases now:** fill what you can, keep `draft`, and end with the directory path and what's missing, most important first. Build nothing.

**Changing an existing prompt:** the eval set must exist and pass before the change; if there is none, this skill runs first. Add cases that pin the intended change before editing the prompt.

Red Flags and Rationalization Prevention tables in house style, seeded from the baseline's verbatim rationalizations (expected: "we'll test once it works", "I'll write a few examples myself", "it's just a small prompt tweak", "the driver has no examples, so I'll generate them").

## `references/graders.md`

One screen: prefer code graders (exact match, JSON schema, regex, numeric tolerance, set membership); model graders only for judgment, each with a rubric of observable criteria and a pass/fail, not a 1–10 score. pass@k: a case passes only if all k runs pass; k = 1 for deterministic settings, 3 by default, 5 where the canvas says errors are costly and unreviewed (automate, agent). Threshold from error tolerance: augment (human reviews) may accept < 100% on normal cases; `refuse` cases always 100%.

## Integration

- `eliciting-needs` step 7: for automate, augment and agent outcomes, hand off to `evaluating-ai-features` with the canvas path, then to `superpowers:brainstorming` with the canvas and the eval set. Classic unchanged.
- README skills table: new row.

## Verification

- `tests/evaluating-ai-features/test_evalset.py`: `new` with and without `--canvas` (criteria imported from a canvas fixture; refuses overwrite); `check` passes on a valid fixture; each of rules 1–6 fails in isolation with a message naming it; `status ready` blocked by a failing check, allowed by a passing one; `status draft` always allowed.
- `tests/evaluating-ai-features/scenarios/`: `run.sh` (setup/prompt/verify, as in the other skills), `BASELINE.md`, `GREEN.md`. Runs use fresh general-purpose subagents, the same method as the existing skills' scenarios. Scenarios:
  1. An approved augment canvas (supplier emails) in `docs/needs/`, plus "build it".
  2. No canvas: "add an LLM step that classifies our service reports by failure cause".
  3. Pressure: "we have no examples yet, write the prompt and we'll test later".
  4. Change: an existing summarisation prompt in the repo, "make the summaries shorter".
  `verify` fails when any file outside `docs/evals/` is written or changed while the eval set isn't `ready` (or doesn't exist). A prompt drafted inside the final message is caught by the manual read.
- The baseline must show a prompt written before any eval in at least half the scenarios; if it doesn't, stop and report before writing SKILL.md.
- GREEN: all four pass `verify` and a manual read; then pressure-test per `superpowers:writing-skills`.
- `uv run pytest`, `claude plugin validate --strict` on both manifests, CI green.

## Out of scope

A runner, model-graded execution, instrumenting existing code or harvesting traces, eval dashboards.
