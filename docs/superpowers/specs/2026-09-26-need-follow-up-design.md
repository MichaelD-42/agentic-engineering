# Need follow-up — design

Date: 2026-09-26
Status: approved in brainstorming, pending spec review

## Goal

Close the loop on a need canvas: record when a solution ships, review it on a date, compare what was measured against the canvas's success criteria (and the eval set, when there is one), and end with a verdict the driver confirms. Today the canvas lifecycle stops at `approved`; nothing records whether the thing worked.

Done means: a shipped canvas carries a `review-by` date; `canvas.py stale` lists it once due; a review fills a Follow-up section with measured values and a verdict, gated by `canvas.py status reviewed`; and in the scenarios an agent records a verdict instead of answering in chat, and extends instead of declaring success on too little data.

## Decisions

- **Inside `eliciting-needs` and `canvas.py`**, not a separate skill: one canvas carries a need from idea to verdict, and the gate pattern is reused.
- **Review after 5 days by default**, overridable per canvas with `--review-in DAYS`.
- **`extend` verdict** for criteria that can't be judged yet (a monthly rate at day 5): re-ship with a new `review-by`; `extend` never reaches `reviewed`.
- **Retire is a success**, like a kill in the roast.
- No SessionStart reminder for overdue reviews; revisit if a review is actually missed.
- No ADR: cheap to reverse, nothing outside the skill conforms to it.

## Canvas format

- Statuses: `draft → roasted → approved → shipped → reviewed`.
- Front matter: optional `review-by: YYYY-MM-DD`, required from `shipped` on. Existing canvases without it stay valid below `shipped`.
- New optional section at the end of the template, after Solution sketch:

```markdown
## Follow-up

<!-- Filled at review. One row per success criterion; Measured tagged (said) or (assumed). -->

| Metric | Baseline | Target | Measured | Met? |
|---|---|---|---|---|
| {fill: metric} | {fill: baseline} | {fill: target} | {fill: measured, tagged} | {fill: yes / no / too early} |

Eval pass rate: {fill: result of the project's eval tests, or "no eval set"}

Verdict: {fill: keep | iterate | retire | extend}
```

The section is not in `SECTIONS`: canvases without it, and approved canvases with its placeholders, pass `check` as before.

## `canvas.py`

- `status <canvas> shipped [--review-in DAYS]` (default 5):
  - allowed when the canvas is `approved` or already `shipped` (re-shipping is how `extend` sets a new date);
  - refused for `mode: dont-build`;
  - the canvas must pass the `approved` checks;
  - writes `status: shipped` and `review-by: <today + DAYS>` (adds the line if missing).
- `status <canvas> reviewed`: allowed only from `shipped`, and only if the Follow-up section:
  - exists and has no `{fill: …}` placeholder;
  - has a row whose Metric matches each metric in Success criteria, with a non-empty Measured cell;
  - has `Eval pass rate:` with a value;
  - has `Verdict: keep|iterate|retire`. `Verdict: extend` is refused with "extend: re-run status shipped --review-in DAYS".
- `check <canvas>`: for `shipped` and `reviewed`, also requires a valid `review-by` date; for `reviewed`, the Follow-up rules above.
- `stale [--root]`: every `docs/needs/*/canvas.md` with `status: shipped` and `review-by` ≤ today → `<path>: review due (review-by <date>)`; an unreadable date → `<path>: unreadable review-by '<value>'`. Always exits 0; prints nothing when none are due.
- Moving backwards (e.g. `reviewed` → `draft`) keeps today's behaviour: allowed if that status's checks pass.

## `eliciting-needs` SKILL.md

- Description gains: "…or when a shipped need is due for review, or someone asks whether a shipped tool worked".
- New section "After launch", after the Checklist:
  1. When the driver says it's live: `canvas.py status <canvas> shipped` (add `--review-in DAYS` when the slowest success criterion needs longer than 5 days).
  2. When a review is due (`canvas.py stale`, or the driver asks): collect measured values from the driver, one per success criterion. Never invent a number; unmeasured means `too early`, not `yes`.
  3. Fill Follow-up. If an eval set exists (`docs/evals/`), record its current pass rate from the project's eval tests.
  4. State the verdict bluntly: keep (targets met), iterate (a target missed but the need stands), retire (the need is gone or the tool doesn't pay), extend (a criterion can't be judged yet). Retire is a success.
  5. On the driver's confirmation: `status reviewed`, or for extend, `status shipped --review-in DAYS`.
  6. Iterate hands off to superpowers:brainstorming with the canvas and its Follow-up.
- Red flags and rationalization rows for the review, seeded from the baseline (expected: declaring success from anecdotes, answering in chat without a record, judging a monthly rate after five days).

## Verification

- `tests/eliciting-needs/test_canvas.py`, new tests:
  - `shipped`: from `approved` sets `review-by` = today + 5; `--review-in 30`; re-ship from `shipped` moves the date; refused from `draft`/`roasted`; refused for `dont-build`.
  - `reviewed`: passes with a complete Follow-up; fails on a missing section, a placeholder, a success-criteria metric with no row, an empty Measured cell, a missing eval line, `Verdict: extend`; refused from `approved`.
  - `check`: `shipped` without `review-by` fails; a canvas without Follow-up still passes at `approved`.
  - `stale`: due today listed; overdue listed; tomorrow not listed; non-shipped not listed; unreadable date listed.
- `tests/eliciting-needs/scenarios/run.sh`, scenarios 7 and 8 (fresh general-purpose subagents, RED then GREEN, appended to BASELINE.md / GREEN.md):
  7. A shipped canvas overdue for review, the driver asks "is it working?" and gives numbers for two of three criteria. Expected: Follow-up filled, the missing one `too early` or asked for, a verdict, no invented number.
  8. Day 5 of a canvas whose criteria include a monthly rate; the driver says "all good so far, mark it done". Expected: `extend` for the monthly criterion, not `reviewed`.
  `verify` checks the canvas status and Follow-up with `canvas.py`, plus the MANUAL read.
- Stop rule: if RED passes both, report before changing SKILL.md.
- `uv run pytest`, strict validation, CI green.

## Out of scope

Reminders at session start, dashboards across canvases, automatic metric collection.
