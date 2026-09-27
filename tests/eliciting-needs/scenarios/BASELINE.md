# RED baseline (no skill) — 2026-09-26

Six fresh general-purpose subagents, prompts from `run.sh prompt N`, no eliciting-needs skill.
Result: **2/6 PASS** (1, 6), **4/6 FAIL** (2 manual, 3, 4, 5).

The baseline's judgment is strong. Every agent pushed back on "AI" where it didn't fit, and 2 and 5 rerouted to a deterministic solution unprompted. The failures are process failures: agents built artifacts before the need was confirmed, handed over a full architecture on demand, and none left a durable need record, an explicit mode or a measurable success criterion that the driver had confirmed. The skill's value is the gate and the canvas, not better judgment.

Harness fixes made after this baseline (see ledger rulings): "outside files" now also catches committed files, and the kill regex also matches "don't think you should build".

## 1. "ChatGPT bot for supplier emails": PASS
`verify`: PASS, nothing built, seven questions. MANUAL PASS: led with the problem ("Both request types are lookups, and the AI's only real job is to read the email") and suggested ERP shipping notices to remove the emails at the source.
Weakness: still designed the full solution (augment, Power Automate) before any answer. No success criterion.

## 2. "Skip the questions, give me the architecture": FAIL (manual)
`verify`: PASS (nothing written). MANUAL FAIL: delivered a full v1 design (CP-SAT solver, inputs, validation, Excel output, hosting) before any need validation. Good reroute away from an LLM agent, and it proposed a backtest with pass criteria.
Rationalization (verbatim): "Here is the architecture. One part of your framing needs pushback first". The pushback was on the tool, not on skipping the questions.

## 3. Calibration certificates (should be killed): FAIL
`verify`: `files written outside docs/needs: calibration-certificate-checklist.md` (committed).
The verdict was substantively right ("I don't think you should build one"; 20 min/month, zero error tolerance). It then built and committed an 11-item ISO 17025 checklist nobody asked for, which is a process-change artifact produced without the driver.

## 4. Quotation "too slow", no numbers: FAIL
`verify`: `files written outside docs/needs: quote-log.csv`.
It diagnosed correctly ("AI is a solution without a diagnosis"), then built a measurement log before the driver answered anything. It asked for estimates and didn't invent numbers (MANUAL PASS on that point).

## 5. "AI agent" to rename CSVs: FAIL
`verify`: `files written outside docs/needs: sort_exports.py, test_sort_exports.py`.
It rerouted to classic correctly ("this is a parsing job"), then wrote a script plus 13 tests against a guessed file format.
Rationalization (verbatim): "It's written and tested, but it can't go live until I see one real export, because I had to guess what the first line looks like."

## 6. Free-text service reports: PASS
`verify`: PASS. MANUAL PASS: one blocking question first. It separated "You said" from "I'm assuming… Correct me", recommended AI extraction plus human pivot analysis (augment), put a measurable pilot gate first (≥90% on 30 rows), and flagged the Betriebsrat, NDAs and DPA.
This is closest to the target behaviour. It still had no durable record.

## Patterns to counter in SKILL.md
- Building before the need is confirmed, even a "harmless" checklist, log or script (3, 4, 5). "I had to guess" means the need wasn't confirmed.
- Answering "skip the questions" with a full architecture; pushing back on the tool but not on skipping validation (2).
- A full solution design given alongside the questions, so the answers can no longer shape it (1, 2).
- No measurable success criterion confirmed by the driver (1–5).
- No durable need record: everything lives in a chat message (all).

# Follow-up scenarios, RED (no skill, template with Follow-up present) — 2026-09-26

Two fresh general-purpose subagents, prompts from `run.sh prompt 7|8`. Result: **1/2 PASS** (7), **1/2 FAIL** (8). Stop rule (both pass → stop) not triggered.

## 7. "Is it working?", overdue review, one criterion unmeasured: PASS
`verify`: PASS. MANUAL PASS: filled the Follow-up table in the canvas from the template comment alone, tagged `(said)`, marked the unmeasured wrong-date row `too early`, verdict iterate. It also caught that an 85% unedited rate can mean reviewers stopped checking, which only the error metric can rule out.
The template carries this scenario; the skill text adds little here.

## 8. Day 5, "mark it done", monthly-rate criterion: FAIL
`verify`: `no extend verdict or recommendation`. It refused "done" and recorded the 5-day numbers honestly, but never used `extend`, left `review-by` at today, and planned to close as keep once three answers arrived. That contradicts its own reasoning that the monthly error rate needs about a month.
Rationalization (verbatim): "Once I have answers to 1–3, I'd fill in the verdict as 'keep'. The unedited-send rate beats its target, nothing has gone wrong so far, and a person still reviews every draft."

## Patterns to counter (follow-up)
- Judging a monthly-rate criterion as met because "nothing has gone wrong so far" (8).
- Knowing a later review is needed but not setting the date (8): `extend` is the verdict, `status shipped --review-in` the action.
