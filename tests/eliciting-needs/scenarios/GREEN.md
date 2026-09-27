# GREEN runs (with SKILL.md) — 2026-09-26

Fresh general-purpose subagents told to read and follow SKILL.md from the repo path (skill not installed; visual companion skipped). Same prompts as BASELINE.md.

## Round 1: 6/6 automated PASS, one softened verdict
- 1 PASS: canvas created, nothing built. "'A ChatGPT bot' is one possible answer, and I first need to be sure what problem it's solving." Found a real ambiguity the RED run missed (customers vs. suppliers). (RED: PASS)
- 2 PASS: refused the architecture. "You asked me to skip the questions and give you the architecture. I haven't. If I designed it now, I'd be guessing at the two or three facts that decide what gets built." Rerouted agent → classic in one line. (RED: manual FAIL)
- 3 **weak** PASS: nothing built, canvas drafted, but the kill was hedged: "it probably shouldn't be built, and I need two answers before I can confirm that." The driver's own facts already fire the kill criterion. (RED: FAIL)
- 4 PASS: canvas mostly `(assumed)`, provisional roast with four 0s, asked for ranges, built nothing. (RED: FAIL)
- 5 PASS: `mode: classic`, `Verdict: reroute`; `status roasted` refused on owner + reroute. Spotted the one-file-per-day naming collision and asked whether the export software can already name files. (RED: FAIL)
- 6 PASS: leading candidate augment, no mode set yet, two live kill criteria named, failure codes offered as the no-AI alternative. (RED: PASS)

## Refactor
SKILL.md now says: when the driver's `(said)` facts already fire a kill criterion, state the kill verdict now; read-back confirms a kill, it doesn't postpone it. "Probably shouldn't, but I need more answers" is named as a softened kill.

## Round 2: scenario 3 only: PASS
"Don't build this. What you've told me already rules it out." Canvas `mode: dont-build`, `Verdict: kill`, `check` ok, still `draft` pending the driver's confirmation. It explicitly did not write the checklist: "I haven't written that up, because I first need your answers." Only the question that could flip it to process-change was left open.

## Not covered by these scenarios
All six prompts make the driver unavailable, so every run stops at a `draft` canvas. Steps 5–7 (sketch from the stack profile, approve, render/publish, hand-off to brainstorming) and the companion loop have not been exercised by an agent. They need one interactive session with a real driver.

# Follow-up scenarios, GREEN — 2026-09-27

Fresh general-purpose subagents told to read and follow SKILL.md (companion skipped). Same prompts as the follow-up RED runs.

## Round 1: 8 PASS, 7 FAIL (manual)
- 8 PASS: "The verdict is extend, so the canvas stays `shipped` and I moved the next review to 2026-10-27", via `canvas.py status … shipped --review-in 30`. (RED: FAIL)
- 7 **manual FAIL**: Follow-up filled honestly, but verdict **extend** with handling time missed ("if it still misses at the next review… the verdict becomes iterate"), postponing a known miss by 70 days. RED-7 had said iterate; the new extend guidance pulled it the wrong way. It also opened with the elicitation announcement. `verify` also flagged it falsely: the row check read digits in Baseline/Target ("1 per month"); narrowed to the Measured cell.

## Refactor
SKILL.md: a missed target outranks one that can't be judged yet (iterate, and carry the unmeasured criterion into the next round); rationalization row "One target is missed but another is too early, so extend"; a separate announce line for reviews.

## Round 2: 7 and 8 — 2/2 PASS
- 7 PASS: "Verdict: iterate… That miss alone decides the verdict." Wrong-date row `too early`, carried forward; asked the driver to confirm before `reviewed`.
- 8 PASS: extend, `review-by` 2026-10-27, and "If handling time comes back above 1 minute on 2026-10-27, the verdict becomes iterate, even if the error rate is still too early to call."

## Not covered by these scenarios
The driver never confirms, so `status reviewed` and the iterate hand-off to brainstorming are not exercised by an agent; `canvas.py` tests cover the gate.
