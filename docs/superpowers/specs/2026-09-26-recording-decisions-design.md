# Spec: `recording-decisions` skill (superpowers-style ADRs)

> Approved 2026-09-26 in plan mode. Refinements made while writing the plan are listed at the end.

## Context
Michael wants a superpowers-style skill that records ADRs in a standard format. Superpowers
specs are per-feature and go stale; ADRs are per-decision and immutable, so they preserve the
"why" after the spec is outdated. Chosen: variant B, integrated with the pipeline (fires at
superpowers decision points). A (standalone) and C (agent-enforceable globs/verify) rejected;
C deferred until B shows which decisions agents break. Added after review: scripts, templates,
tests, hooks, stale detection.

This plan file is the brainstorming spec. Next step after approval: superpowers:writing-plans,
then the writing-skills TDD loop.

## Research basis
- MADR 4.0 (adr.github.io/madr): front matter + required context/options/outcome; minimal/full.
- arXiv 2604.27333: Nygard best for concision, MADR for structured/contested decisions.
- AgDR (github.com/me2resh/agent-decision-record): Y-statement adopted; agent/model metadata
  rejected (git records it).
- ECC architecture-decision-records skill: prior art for docs/adr + index + draft-first.
- Claude Code docs (code.claude.com/docs/en/skills, /hooks), verified:
  - Skill frontmatter `hooks:` register **when the skill is invoked** and stay for the session.
    So nothing loads until the skill fires, which avoids context flooding.
  - `` !`cmd` `` in SKILL.md runs at skill load and inlines the output.
  - `${CLAUDE_SKILL_DIR}` is documented for skill content and `allowed-tools` only. **Unverified
    in frontmatter hook commands.** Spike first (Task 0).
  - Plugin skills use the same frontmatter hooks, so the plugin needs no separate hooks.json.

## Layout: build in workspace as a plugin, symlink into profile
```
/home/michael/workspace/claude_workspace/recording-decisions/   (git init; local only)
  .claude-plugin/plugin.json
  skills/recording-decisions/
    SKILL.md                  # hooks in frontmatter
    templates/adr-minimal.md  # default
    templates/adr-full.md     # ≥3 options or stakeholder disagreement
    scripts/adr.py            # stdlib-only Python 3.12 CLI
    scripts/hook-validate.sh  # PostToolUse → adr.py check <file>
    scripts/hook-immutable.py # PreToolUse guard
  tests/
    test_adr.py               # stdlib unittest (pytest not installed)
    fixtures/                 # ADR dirs: valid, broken links, gaps, dup numbers, dead refs, overdue review
    scenarios/                # 5 pressure-scenario repo setups
    run-scenarios.sh          # builds scenario repos in $TMPDIR for RED/GREEN runs
```
Personal install: `ln -s <workspace>/recording-decisions/skills/recording-decisions ~/.claude/skills/recording-decisions`
(one source of truth; needs Michael's approval since ~/.claude/skills is sandbox-protected).
Marketplace later = add marketplace entry; no file moves.

## Behavior
**Triggers (description):** "Use when choosing between alternative approaches, libraries, data
models, or architectural patterns — including the approach choice in brainstorming — or when your
human partner says to record, supersede, review, or revisit a decision."

**Gate (Iron Law): ADR only if ≥2 of 3 hold:** costly to reverse (data migration, public
interface, >1 component rewrite); crosses a boundary (others must conform); real rivals (≥2
viable options weighed, rejection reason stated). Otherwise one sentence in the spec.
**Autonomy:** one-line proposal → on yes, `adr.py new` as `proposed` → on approval, `accepted`.

**Template (MADR 4.0 minimal + Y-statement, ≤ ~60 lines):** front matter `status`
(proposed|accepted|rejected|deprecated|superseded by ADR-NNNN), `date`, `decision-makers`,
`review-by` (default: accepted date + 12 months; custom field), `consulted`/`informed` only if
real. Title = the decision; Y-statement line; Context and Problem Statement; Considered Options
(one pro/con line each); Decision Outcome + Consequences (good/bad); optional Confirmation.
Full template adds Decision Drivers + separate Pros and Cons.

**Lifecycle:** accepted = immutable except `status` and `review-by`. Change = `adr.py supersede`.
Spec links `ADR-NNNN` instead of restating rationale.

**ADR dir detection:** `.adr-dir` → `docs/adr` → `docs/decisions` → `doc/architecture/decisions`;
else create `docs/adr/` + `README.md` index. Existing dir's own template wins.

## `adr.py` subcommands
- `new "<title>" [--full]`: next 4-digit number, slug, template fill, index row.
- `supersede <NNNN> "<title>"`: new ADR + `Supersedes`, old status → `superseded by ADR-MMMM`, index.
- `accept <NNNN>`: status → accepted, set `review-by`.
- `check [files…]`: front matter + valid status; unique numbers; bidirectional supersede links;
  index ↔ files; line cap; in git: body diff on accepted ADR vs HEAD is an error. Exit 1 on errors.
- `stale`: accepted ADRs with `review-by` past today, or backticked paths that no longer exist.
  Output is review candidates, not verdicts.
- `digest`: one line per accepted ADR (`ADR-NNNN title: Y-statement`), capped at 30 lines,
  plus a count of the rest. Empty output when there's no ADR dir.
Before writing: search for an existing MADR CLI to port (adr-tools is Nygard-only); port if one fits.

## Hooks (all in SKILL.md frontmatter; active only after skill invoked)
1. **PostToolUse** `Write|Edit` → `hook-validate.sh`: exits 0 unless file is in the ADR dir;
   then `adr.py check <file>`; errors → exit 2 with stderr fed back to Claude.
2. **PreToolUse** `Edit|Write` → `hook-immutable.py`: if target is an accepted ADR and the change
   touches anything except `status:`/`review-by:` lines → block (exit 2) with "supersede instead".
3. **Digest** replaces SessionStart (a skill hook can't fire at session start):
   `` !`python3 ${CLAUDE_SKILL_DIR}/scripts/adr.py digest` `` in SKILL.md loads accepted
   decisions when the skill loads. Trade-off: agents only see decisions once the skill fires.
   No global SessionStart, per the no-flooding requirement.
4. **Pre-commit:** SKILL.md offers a snippet running `adr.py check`; never auto-installed.

## Tasks (writing-plans will expand)
0. Spike: minimal skill with frontmatter PostToolUse hook echoing `${CLAUDE_SKILL_DIR}`; confirm
   substitution in hook commands. If absent, use `$HOME/.claude/skills/recording-decisions/...`
   for personal install and `${CLAUDE_PLUGIN_ROOT}/skills/...` for the plugin build. Throwaway.
1. `git init` workspace plugin dir; plugin.json; templates.
2. `adr.py` TDD via unittest fixtures, one subcommand at a time.
3. Hook scripts + unittest (feed sample hook JSON on stdin, assert exit code/stderr).
4. RED: run 5 scenarios with fresh subagents *without* skill; record rationalizations verbatim.
5. Write SKILL.md (superpowers structure: Overview, Iron Law gate, checklist, lifecycle,
   red-flags for under- and over-recording, rationalization table from step 4).
6. GREEN/REFACTOR: rerun scenarios with skill until all pass; symlink install (with approval).

## Verification
- `python3 -m unittest discover tests -v`: all pass, output shown.
- Scenarios (checked on written files, not agent reports):
  1. Postgres vs SQLite event store → proposal line, `docs/adr/0001-*.md` proposed, index row.
  2. Formatter choice → no ADR.
  3. ADR 0003 reversed → 0004 created, 0003 `superseded by ADR-0004`, index updated.
  4. `.adr-dir` → `doc/architecture/decisions` → followed, including its template.
  5. "Just pick, we're in a hurry" → proposal still issued.
- Hooks live: invoke skill in a scratch repo, try editing an accepted ADR body → blocked;
  write a malformed ADR → check error fed back.
- Scratch scenario repos deleted afterward.

## Refinements while writing the plan
- **Supersede timing:** `supersede` creates the new ADR with `Supersedes ADR-NNNN`, and the old ADR's
  status flips to `superseded by ADR-MMMM` when the new one is **accepted** (`adr.py accept`).
  Flipping it at proposal time would leave a lie behind if the proposal is rejected.
- **Immutability:** applies to every non-`proposed` status (accepted, superseded, deprecated, rejected), not
  only accepted. Mutable fields: `status`, `date` (MADR: last updated), `review-by`.
- **Hook scripts** are Python (`hook_validate.py`, `hook_immutable.py`) importing `adr.py`, so hook JSON parsing
  and ADR logic are shared.
- **Test fixtures** are built in code inside `tempfile` repos instead of a `fixtures/` tree.
- **Formats:** reading supports MADR front matter and Nygard/adr-tools `## Status` sections, so existing
  adr-tools repos pass `check`. `review-by` exists only in front matter; Nygard ADRs get dead-reference
  staleness only.
- `stale` exits 1 when there are candidates (usable in CI); `check` prints `ADR check passed (N ADRs)`.
- Existing MADR CLIs reviewed: madr-tools-python (last push 2020, pre-MADR 4) and nioe/madr-tools
  (Node; no check/stale/digest). Not ported.
