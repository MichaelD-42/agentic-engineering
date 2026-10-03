---
name: eliciting-needs
description: Use when someone brings a first idea for an AI use case, tool, bot, agent or automation ("we need a ChatGPT for…", "build me an AI that…", "can AI speed up…") before any solution is designed, or when asked to clarify, document, roast or validate what a use case actually needs, or when a shipped need is due for review or someone asks whether a shipped tool worked
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/canvas.py *)
---

# Eliciting Needs

## Overview

A first idea is usually a solution in disguise. "A ChatGPT for supplier emails" is not the need. The need might be "certificate requests take two people an hour a day". The fix for that might be a shared-folder link, a script or an LLM. This skill finds the need, writes it on a canvas, roasts it, and only then sketches a solution.

**Core principle:** Get the need right before anyone chooses how to meet it.

The person driving this session is usually an engineer, but not a software engineer. Use plain language. Explain any software term in one line the first time you use it.

**Announce at start:** "I'm using the eliciting-needs skill to work out what you actually need before we design anything."

## The Iron Law

```
NO SOLUTION UNTIL THE NEED SURVIVES THE ROAST
```

Until `canvas.py status <canvas> roasted` succeeds:
- write nothing outside `docs/needs/` (companion screens excepted): no script, checklist, log, template or prototype;
- give no architecture, no design, and no tool names.

This holds when the driver asks for them. It holds when the thing is "just a small helper". It holds when you are sure you already know the answer. A direction in one sentence is fine ("this looks like a job for a plain script, not an agent — the roast will confirm"). A design is not.

## Checklist

1. **Capture:** Quote the idea verbatim. Run `python3 ${CLAUDE_SKILL_DIR}/scripts/canvas.py new "<short title>" --owner "<driver, if they will own it>"`. Offer the visual companion (below).
2. **Elicit:** Pick the weakest or emptiest cell and ask **one** plain-language question, using a probe from `references/probes.md`. Write the answer into the canvas, tagged `(said)` or `(assumed)`, and re-render. Repeat until every cell up to Open questions is filled; `canvas.py check <canvas>` lists what is still missing. Never promote `(assumed)` to `(said)` without the driver confirming. In Mermaid blocks, keep every label in double quotes with the tag inside, like `A["Mail arrives (said)"]`; an unquoted `(` breaks the diagram.
3. **Read back:** Read the Actual need sentence and the Success criteria back to the driver, and apply their corrections. This is the validation step. Don't skip it.
4. **Classify and roast:** Choose the mode with `references/ai-fit.md`, then score every cell with `references/roast-rubric.md` and write the Roast section. Present it bluntly. A 0 sends you back to step 2. A `reroute` means change the mode and roast again. A `kill` means recommend `dont-build` or `process-change`, which is a successful outcome and should be presented as one. Then run `canvas.py status <canvas> roasted`. Its output is the gate.
5. **Sketch:** Write 1–2 options in the chosen mode, using the stack profile (`docs/stack.md` → `~/.claude/stack.md` → `${CLAUDE_SKILL_DIR}/templates/stack-profile.md`), and say which profile you used. For each option give the tools, the build and run cost (per-run LLM cost for runtime modes), the risks, the non-goals, and any deviation from the profile with its reason. A runtime-AI option always names the classic alternative it beat and why.
6. **Approve:** Once the driver approves, run `canvas.py status <canvas> approved`, then `canvas.py render <canvas>`. Offer to publish `canvas.html` as an artifact, and publish only on a yes. For `dont-build`/`process-change`, the Solution sketch states the recommendation and why ("No build: 20 min/month doesn't justify a tool; keep the manual check"), plus the process change if there is one.
7. **Hand off:** For automate, augment and agent outcomes, invoke evaluating-ai-features with the canvas path, then superpowers:brainstorming with the canvas and the eval set. For classic, invoke superpowers:brainstorming with the canvas path. For `dont-build`/`process-change`, stop at step 6. The driver builds the checklist or process change, or asks for it, after approval.

**When the driver can't answer now:** fill what you can, tag your guesses `(assumed)`, and end with the canvas path and your questions, most important first. The canvas stays `draft`. Do not "get a head start" by building anything.

**When the driver's own `(said)` facts already fire a kill criterion** (for example, 20 minutes a month of work, or nobody but them to maintain it): say so now, as a verdict: "Don't build this, because…". Then ask only the questions that could overturn it. Read-back confirms a kill; it does not postpone it. "Probably shouldn't, but I need more answers" is a softened kill.

## After launch

**Announce at a review:** "I'm using the eliciting-needs skill to review this shipped need against its success criteria."

1. **Ship:** when the driver says it's live, run `canvas.py status <canvas> shipped`. Add `--review-in DAYS` when the slowest success criterion needs longer than 5 days to show (a monthly rate needs about 30).
2. **Review when due:** `canvas.py stale` lists canvases whose review is due; the driver may also just ask "is it working?". Collect the measured value for every success criterion from the driver. Never invent one: a criterion nobody measured is `too early`, not met.
3. **Fill Follow-up:** one row per success criterion, Measured tagged `(said)` or `(assumed)`. If `docs/evals/` has an eval set for this need, record the current pass rate of its tests.
4. **Verdict, bluntly:** keep (targets met), iterate (a target missed but the need stands), retire (the need is gone or the tool doesn't pay), extend (a criterion can't be judged yet). Retire is a success, like a kill. A criterion whose baseline is a rate per month can't be judged in days: zero errors in five days is what the old rate predicts anyway, so the verdict is extend, not keep. A missed target outranks one that can't be judged yet: if any criterion is missed, the verdict is iterate, and the unmeasured one goes into the next round's review.
5. **Close:** `canvas.py status <canvas> reviewed` only on the driver's confirmation. For extend, write `Verdict: extend` and run `canvas.py status <canvas> shipped --review-in DAYS` yourself; it closes nothing, it only sets the next date.
6. **Iterate** hands off to superpowers:brainstorming with the canvas and its Follow-up.

## Visual companion

This needs superpowers. Find the newest `start-server.sh`:

```bash
ls -d ~/.claude/plugins/cache/*/superpowers/*/skills/brainstorming/scripts/start-server.sh | sort -V | tail -1
```

Offer it once, as its own message. On a yes, start it with `--project-dir <repo> --open` and follow that skill's `visual-companion.md` for the loop. After every canvas change, run `canvas.py render <canvas> --out <screen_dir>/canvas-<n>.html` with a new `n` each time, since the companion shows the newest file. If superpowers is missing or the offer is declined, run `canvas.py render <canvas> --open` once; the driver reloads the page themselves after each change.

## Solution modes

| Mode | AI where? | Meaning |
|---|---|---|
| automate | runtime | LLM step in a fixed pipeline, no human review |
| augment | runtime | LLM drafts or suggests, a human decides |
| agent | runtime | LLM chooses steps and calls tools toward a goal |
| classic | build time | Claude builds a script/tool/app; no LLM in production |
| process-change | — | change how people work; nothing to build |
| dont-build | — | the need doesn't justify a build |

The default is classic, unless the task needs judgment on unstructured input. Hybrids take one primary mode, and the to-be flow marks which steps call an LLM.

## Red Flags — STOP

- A tool or product name in the request, treated as the need
- Writing any file outside `docs/needs/` while the canvas is `draft`: a script "to show them", a checklist, a measurement log
- "I had to guess the format / the constraints", which means the need isn't confirmed and it's too early to build
- Questions and a full design in the same message, so the answers can no longer shape the design
- "They said skip the questions", answered with the architecture instead of the canvas
- Inventing numbers the driver didn't give, or tagging them `(said)`
- Softening a kill verdict to be helpful
- Picking agent or automate for structured, rule-based input
- Forcing free-text or judgment-heavy work into classic
- Asking several questions at once while the driver is present

**After launch**
- Answering "is it working?" in chat without filling the canvas's Follow-up
- Calling a criterion met that nobody measured
- "Nothing has gone wrong so far" as evidence for a monthly-rate target after days
- Knowing a later review is needed but leaving `review-by` where it is

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "They know what they want" | They know what they asked for. The roast is how you both find out whether it's what they need. |
| "They said skip the questions" | Show them the canvas instead. What they already told you fills most of it, and the roast takes minutes. An architecture built on unconfirmed constraints is the slow path. |
| "It's just a small checklist / log / script" | It's a solution. It's also an answer to a question nobody asked yet. Put it in the sketch, after the roast. |
| "I'll build it now so it's ready when they answer" | You'll build it against a guess. That's what "I had to guess the format" means. |
| "I'll give the design and the questions together" | Then the design ignores the answers. Ask, then design. |
| "Asking questions is slow" | Building the wrong thing is slower. One question at a time, and each one targets the weakest cell. |
| "I'll fill in reasonable numbers" | Tag them `(assumed)` and ask. An invented number that nobody notices becomes the spec. |
| "Killing it feels unhelpful" | A clear "don't build this" saves them weeks. That is the helpful answer. |
| "An agent is more impressive" | A script that's always right beats an agent that's usually right. Pick the least AI that meets the need. |
| "check is just a formality" | `check` is the gate. Fix the canvas; don't route around it. |
| "Once I have a few answers, I'd fill in the verdict as keep: nothing has gone wrong so far" | Nothing going wrong in five days is what the old monthly rate predicts. Extend, and set the date. |
| "One target is missed but another is too early, so extend" | Extend postpones the missed target too. A miss is known now: iterate. |
