# Spec: `eliciting-needs` skill (agentic-engineering plugin)

> Brainstormed 2026-09-26 in plan mode. This plan file is the brainstorming spec. After approval:
> copy to `agentic-engineering/docs/superpowers/specs/2026-09-26-eliciting-needs-design.md`,
> commit, then superpowers:writing-plans, then the writing-skills TDD loop.

## Context
Non-software engineers driving Claude Code bring AI use cases as a first idea, often a solution in disguise ("we need a
ChatGPT for supplier emails"). Building from that idea ships the wrong thing. The skill applies
requirements-engineering elicitation to extract the real need, documents and visualizes it,
roasts it, and only then sketches a solution with preferred tooling before handing off to
superpowers:brainstorming for the real design.

Decided with Michael:
- **Host:** Claude Code, driven directly by the person with the need — typically an engineer,
  but not a software engineer (mechanical, process, electrical, ops). One driver, no separate
  expert: plain language throughout, no software jargon without a one-line gloss, the driver
  approves every gate. Roast has no second human, so the rubric does the adversarial work.
- **Solution modes:** the AI-fit step classifies how AI helps, in two families:
  - *AI at runtime* (an LLM runs in production): **automate** (LLM step in a fixed pipeline, no
    human review), **augment** (LLM drafts/suggests, human decides), **agent** (LLM chooses
    steps and calls tools toward a goal).
  - *AI at build time* (Claude builds it, no LLM in production): **classic solution** —
    script, tool, or application, deterministic.
  - Plus **process change** and **don't build**.
  Default bias: classic solution unless the task needs judgment on unstructured input.
  Hybrids are allowed: one primary mode, with the to-be flow marking which steps call an LLM.
- **Architecture scope:** 1–2 plain-language solution sketches + handoff to brainstorming;
  no full architecture in this skill.
- **Tooling:** stack profile file (project `docs/stack.md` → `~/.claude/stack.md` → shipped default).
- **Visuals:** live superpowers visual companion during the session + HTML artifact as take-away;
  markdown canvas is the source of truth, HTML is rendered from it.
- **Packaging:** new plugin folder in this workspace, extracted to a marketplace later.
- **Approach:** B, canvas-driven (rejected: A linear phases — hides the roast→re-elicit loop;
  C subagent roaster — cost, and conflicts with "no subagent checking own work").

## Layout
```
/home/michael/workspace/claude_workspace/agentic-engineering/   (git init; local only)
  .claude-plugin/plugin.json
  skills/eliciting-needs/
    SKILL.md
    templates/need-canvas.md
    templates/stack-profile.md
    references/probes.md
    references/roast-rubric.md
    references/ai-fit.md
    scripts/canvas.py          # stdlib-only Python 3.12
  tests/test_canvas.py
  tests/scenarios/             # pressure scenarios (RED baseline / GREEN)
  pyproject.toml               # uv, pytest dev dep, package=false (as recording-decisions)
```
Per use case output in the target project: `docs/needs/YYYY-MM-DD-<slug>/canvas.md` (truth)
+ `canvas.html` (rendered; published as artifact only after the engineer confirms).

## Canvas (`templates/need-canvas.md`)
Frontmatter: `title`, `date`, `status: draft|roasted|approved`, `owner`,
`mode: automate|augment|agent|classic|process-change|dont-build` (empty until step 8).
Sections (fixed H2s; every claim tagged *said* (by the driver) or *assumed* (by Claude)):
1. Original idea (verbatim quote)
2. Actual need — JTBD: *[actor] needs to [job] so that [outcome]; today blocked by [obstacle]*
3. Actors (has problem / pays / operates / affected)
4. As-is process (Mermaid flowchart, pain points marked)
5. Cost of the problem (frequency × time/money/errors, confidence)
6. Success criteria (baseline → target, measurable)
7. Context diagram (Mermaid: boundary, actors, data sources)
8. Solution mode (per `ai-fit.md`): automate | augment | agent | classic | process change |
   don't build, with the deciding factors — input structured or not, judgment needed, error
   tolerance, verifiability of output, volume/frequency, data availability, cost per run.
   For hybrids: to-be flow (Mermaid) marks LLM steps.
9. Constraints & risks (GDPR/data protection, compliance, budget, ownership)
10. Open questions
11. Roast (score table, kill-criteria check, verdict)
12. Solution sketch (locked until `roasted`)

## `canvas.py`
- `new "<title>"` — scaffold `docs/needs/<date>-<slug>/canvas.md` from template.
- `check <path>` — exit 1 with one line per problem: missing section, `{…}` placeholder,
  success criteria without number+unit, status `roasted`/`approved` without roast scores or
  without a valid `mode`, sketch filled while `draft`.
- `status <path> roasted|approved` — transitions only if `check` passes for that target.
- `render <path>` — single self-contained HTML: raw markdown embedded (escaped), rendered
  client-side by marked + mermaid from cdn.jsdelivr.net. Same file serves as companion screen
  (full document) and artifact.

## Session flow (SKILL.md checklist)
1. Capture idea verbatim; `canvas.py new`; start the superpowers companion (ADR-0001; discover highest
   installed `superpowers/*/skills/brainstorming/scripts/start-server.sh`; fallback: render +
   `xdg-open`).
2. Elicit loop: weakest cell → one plain-language question using a probe from `probes.md`
   (5 Whys, day-in-the-life, cost of doing nothing, "without AI?", counterexample) → update
   canvas → render → companion refresh.
3. Read-back: need statement + success criteria read back to the driver; corrections applied.
4. Classify the solution mode (canvas §8), then roast per `roast-rubric.md`; cells scoring 0
   loop back to step 2; kill criteria → don't build or process change (valid outcomes).
5. Sketch: 1–2 options in the chosen mode from the stack profile — tools, costs (incl. per-run
   LLM cost for runtime modes), risks, non-goals, deviations from profile with reason. A
   runtime-AI sketch always names the classic alternative it beat and why.
6. Approve (driver) → `status approved` → `render` → offer artifact publish (confirm).
7. Hand off: invoke superpowers:brainstorming with the canvas path.

**Iron law:** `NO SOLUTION UNTIL THE NEED SURVIVES THE ROAST`.
Red flags: tool name in the request; engineer pushing to architecture; "assumed" silently
promoted to "said"; sketch before `roasted`; softening a kill verdict.

## Roast rubric
Per cell 0 (missing / solution in disguise), 1 (vague or assumed), 2 (specific, said, verifiable).
Pass: no 0s; need statement, success criteria, AI fit each at 2.
Kill criteria (override score): no measurable success; problem cost below plausible build+run
cost; required data absent or unusable legally; no owner after launch.
Mode challenges (reroute, not kill): runtime-AI mode where a classic solution does the job
(structured input, rules expressible) → classic; automate/agent with low error tolerance and
unverifiable output → augment or classic; agent where a fixed pipeline suffices → automate.
Blunt about the idea, not the person; every hit names the fixing question.

## Stack profile (`templates/stack-profile.md`)
Two parts. Runtime AI: LLM/provider, agent framework, workflow/integration, evals/observability.
Classic: language/runtime for scripts, app/UI framework, data/storage, packaging/distribution
(how a non-software engineer runs it), hosting. Shipped default is opinionated; exact contents decided in the
plan. Lookup: `docs/stack.md` → `~/.claude/stack.md` → shipped default; sketch says which was used.

## Error handling
`check` failures are information: fix the canvas, don't route around it. Companion missing →
static HTML. No profile → default, stated in sketch. Nothing else.

## Verification
- Step 0: prior-art search (`gh auth` needed; `gh search code/repos` for elicitation/requirements
  skills), port anything proven.
- `uv run pytest` for `canvas.py`: new, every check rule, status gates, render output (escaped
  markdown, both CDN tags).
- Pressure scenarios via superpowers:writing-skills (RED without skill, GREEN with): expert opens
  with a tool name; hurried driver wants architecture; idea that should be killed; driver who
  can't quantify; "build me an AI agent" where a script solves it (must reroute to classic);
  unstructured-input task (must not be forced into classic). Pass = no sketch before roast
  passes, kill verdict delivered, mode rerouted when warranted, assumptions stay tagged.
- Manual: run a session in a scratch project, confirm companion refreshes and `canvas.html`
  renders Mermaid.
- Companion reuse vs vendoring: recorded as ADR-0001.
