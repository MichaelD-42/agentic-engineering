# Marketplace Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn this repo into an empty-but-valid Claude Code plugin + marketplace named `agentic-engineering`, with version tooling and contributor docs.

**Architecture:** The repo root is the plugin; `.claude-plugin/marketplace.json` lists it with `"source": "./"` (ADR-0001). Skills will live in `skills/<name>/SKILL.md`; none ship yet. A ported superpowers `bump-version.sh` keeps the two manifest versions in sync.

**Tech Stack:** JSON manifests, Bash + `jq`, `shellcheck`, `claude plugin validate`.

**Spec:** `docs/superpowers/specs/2026-09-26-marketplace-bootstrap-design.md`

## Global Constraints

- Plugin name, marketplace name: `agentic-engineering`. Install id: `agentic-engineering@agentic-engineering`.
- Repo URL in manifests/docs: `https://github.com/MichaelD-42/agentic-engineering`.
- Version: `0.1.0` in `.claude-plugin/plugin.json#version` and `.claude-plugin/marketplace.json#plugins.0.version`.
- Author/owner: `{"name": "Michael Dold"}` — no email anywhere.
- Claude Code only: no `.codex-plugin`, `.cursor-plugin`, `gemini-extension.json`, etc.
- No hooks, no skills, no bootstrap skill in this change.
- `LICENSE` is not modified.
- Conventional commits; every commit message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Work on branch `feat/marketplace-bootstrap` (already created, holds spec + ADR commits).

## Review Focus

- `.gitignore` must not ignore anything under `.claude-plugin/` or `skills/.gitkeep` → Task 4 checks with `git check-ignore`.
- `bump-version.sh` run from a directory other than the repo root must still find `.version-bump.json` → Task 3 runs it from `/`.
- `bump-version.sh` given a non-version argument (`banana`) must exit non-zero and change nothing → Task 3 tests it.
- `--audit` must not flag the spec/plan/release notes (which legitimately contain `0.1.0`) as undeclared → Task 3 excludes them and asserts "All clear".
- `claude plugin validate --strict .` must pass with an empty `skills/` → Task 2 and Task 5.

---

### Task 1: Wipe the old collection

**Files:**
- Delete: `skills/` (all 9 skills), `AGENTS.md`

- [ ] **Step 1: Confirm what is being deleted**

Run: `git ls-files skills AGENTS.md | wc -l`
Expected: `42` (41 skill files + AGENTS.md). If it differs, stop and report — someone changed the tree.

- [ ] **Step 2: Delete**

```bash
git rm -rq skills AGENTS.md
```

- [ ] **Step 3: Verify**

Run: `git ls-files`
Expected exactly: `.gitignore`, `LICENSE`, `README.md`, and the `docs/` files (ADR README, ADR-0001, spec, this plan if committed).

- [ ] **Step 4: Commit**

```bash
git commit -q -m "chore: remove legacy skill collection

Superseded by the agentic-engineering plugin layout (ADR-0001).
The removed skills remain in git history.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Plugin and marketplace manifests

**Files:**
- Create: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `skills/.gitkeep`

**Interfaces:**
- Produces: the JSON field paths `version` (plugin.json) and `plugins.0.version` (marketplace.json) that Task 3's `.version-bump.json` declares.

- [ ] **Step 1: Run the validator to see it fail**

Run: `claude plugin validate --strict .`
Expected: non-zero exit, no manifest found.

- [ ] **Step 2: Write `.claude-plugin/plugin.json`**

```json
{
  "name": "agentic-engineering",
  "description": "Skills for agentic engineering: disciplined, test-first, evidence-based work with coding agents",
  "version": "0.1.0",
  "author": {
    "name": "Michael Dold"
  },
  "homepage": "https://github.com/MichaelD-42/agentic-engineering",
  "repository": "https://github.com/MichaelD-42/agentic-engineering",
  "license": "MIT",
  "keywords": [
    "skills",
    "agentic-engineering",
    "tdd",
    "workflows",
    "best-practices"
  ]
}
```

- [ ] **Step 3: Write `.claude-plugin/marketplace.json`**

```json
{
  "name": "agentic-engineering",
  "description": "Marketplace for the agentic-engineering skills plugin",
  "owner": {
    "name": "Michael Dold"
  },
  "plugins": [
    {
      "name": "agentic-engineering",
      "description": "Skills for agentic engineering: disciplined, test-first, evidence-based work with coding agents",
      "version": "0.1.0",
      "source": "./",
      "author": {
        "name": "Michael Dold"
      }
    }
  ]
}
```

- [ ] **Step 4: Create the skills directory placeholder**

```bash
mkdir -p skills && : > skills/.gitkeep
```

- [ ] **Step 5: Validate**

Run: `claude plugin validate --strict . ; echo "exit=$?"`
Expected: `exit=0`. If `--strict` warns about a field, fix the manifest (do not drop `--strict`); if it rejects `skills/` being empty, report back rather than adding a dummy skill.

Also run: `claude plugin validate --strict .claude-plugin/marketplace.json ; echo "exit=$?"`
Expected: `exit=0`.

- [ ] **Step 6: Commit**

```bash
git add .claude-plugin skills/.gitkeep
git commit -q -m "feat: add agentic-engineering plugin and marketplace manifests

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Version bump tooling

**Files:**
- Create: `.version-bump.json`, `scripts/bump-version.sh` (ported from obra/superpowers @ `8ca22dba9a94f28898bbce59f2537ff4d87c747d`, MIT)

**Interfaces:**
- Consumes: `version` in plugin.json, `plugins.0.version` in marketplace.json (Task 2).
- Produces: `scripts/bump-version.sh <X.Y.Z> | --check | --audit`, referenced by AGENTS.md and README (Task 4).

- [ ] **Step 1: Run the check to see it fail**

Run: `scripts/bump-version.sh --check`
Expected: `no such file or directory`.

- [ ] **Step 2: Write `.version-bump.json`**

```json
{
  "files": [
    { "path": ".claude-plugin/plugin.json", "field": "version" },
    { "path": ".claude-plugin/marketplace.json", "field": "plugins.0.version" }
  ],
  "audit": {
    "exclude": [
      "RELEASE-NOTES.md",
      "docs",
      ".git",
      ".version-bump.json",
      "bump-version.sh"
    ]
  }
}
```

(`docs` holds the spec and this plan, which mention `0.1.0` by design. Excludes are passed to `grep --exclude`/`--exclude-dir`, which match basenames, so the script is listed as `bump-version.sh`.)

- [ ] **Step 3: Fetch the upstream script verbatim**

```bash
mkdir -p scripts
gh api 'repos/obra/superpowers/contents/scripts/bump-version.sh?ref=8ca22dba9a94f28898bbce59f2537ff4d87c747d' --jq .content | base64 -d > scripts/bump-version.sh
chmod +x scripts/bump-version.sh
```

- [ ] **Step 4: Strip YAML support and add attribution**

Edit `scripts/bump-version.sh` (use the Edit tool, exact matches):

1. Replace the first line after the shebang, `#`, with:
```bash
#
# Ported from obra/superpowers (MIT, © Jesse Vincent)
# https://github.com/obra/superpowers/blob/8ca22dba9a94f28898bbce59f2537ff4d87c747d/scripts/bump-version.sh
# Changes: YAML manifest support removed (no YAML manifests here).
#
```
2. Delete the whole `read_yaml_field() { … }` and `write_yaml_field() { … }` functions.
3. Delete the line `    *.yaml) read_yaml_field "$@" ;;` and the line `    *.yaml) write_yaml_field "$@" ;;`.

Keep `require_tool` (still used by `preflight_manifests`). Change nothing else.

Run: `grep -n -i yaml scripts/bump-version.sh`
Expected: only the header comment line.

- [ ] **Step 5: Lint**

Run: `shellcheck scripts/bump-version.sh; echo "exit=$?"`
Expected: `exit=0`. If upstream code triggers warnings, fix them minimally and note it in the commit body.

- [ ] **Step 6: Check, from the repo root and from elsewhere**

Run: `scripts/bump-version.sh --check; echo "exit=$?"`
Expected: both files listed at `0.1.0`, `All declared files are in sync at 0.1.0`, `exit=0`.

Run: `(cd / && "$OLDPWD/scripts/bump-version.sh" --check >/dev/null; echo "exit=$?")`
Expected: `exit=0`.

- [ ] **Step 7: Audit is clean**

Run: `scripts/bump-version.sh --audit`
Expected: ends with `No undeclared files contain the version string. All clear.`

- [ ] **Step 8: Behaviour tests in a scratch copy (repo untouched)**

```bash
S="$TMPDIR/bump-test" && rm -rf "$S" && mkdir -p "$S"
cp -r .claude-plugin .version-bump.json scripts "$S"/   # script resolves REPO_ROOT from its own path
cd "$S"
# drift is detected
jq '.version = "9.9.9"' .claude-plugin/plugin.json > p && mv p .claude-plugin/plugin.json
scripts/bump-version.sh --check; echo "drift-exit=$?"          # expect DRIFT DETECTED, drift-exit=1
# invalid version rejected, nothing written
scripts/bump-version.sh banana; echo "bad-exit=$?"             # expect error, bad-exit=1
jq -r .version .claude-plugin/plugin.json                       # expect 9.9.9
# bump rewrites both
scripts/bump-version.sh 0.1.1 >/dev/null
jq -r .version .claude-plugin/plugin.json                       # expect 0.1.1
jq -r '.plugins[0].version' .claude-plugin/marketplace.json     # expect 0.1.1
cd - >/dev/null && rm -rf "$S"
git status --short                                              # expect only the two new untracked files
scripts/bump-version.sh --check | tail -1                       # expect in sync at 0.1.0 (repo untouched)
```

- [ ] **Step 9: Commit**

```bash
git add .version-bump.json scripts/bump-version.sh
git commit -q -m "chore: add version bump script ported from superpowers

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Repo docs and hygiene files

**Files:**
- Create: `AGENTS.md`, `CLAUDE.md`, `RELEASE-NOTES.md`, `.gitattributes`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/bug_report.md`, `.github/ISSUE_TEMPLATE/feature_request.md`
- Modify: `README.md` (full rewrite), `.gitignore`

**Interfaces:**
- Consumes: install id and repo URL (Global Constraints); `scripts/bump-version.sh` (Task 3).

- [ ] **Step 1: Write `README.md`**

````markdown
# agentic-engineering

A Claude Code plugin of skills for agentic engineering: getting coding agents to work the way a disciplined engineer does. Design before code, a failing test before the fix, evidence before any claim of "done".

Skills are instruction sets that Claude Code loads when their trigger matches the task in front of it. This plugin bundles them so one install gives you the whole workflow.

## Installation

```text
/plugin marketplace add MichaelD-42/agentic-engineering
/plugin install agentic-engineering@agentic-engineering
```

To update: `/plugin marketplace update agentic-engineering`.

## Skills

None yet. This release bootstraps the plugin and marketplace; skills are added in upcoming releases and will be listed here.

| Skill | Use when |
|-------|----------|
| — | — |

## Principles

The skills here share a few convictions. Evidence over assumption: run the command and read the output before claiming anything. Root cause over symptom: investigate before patching. Test first: if you didn't watch the test fail, you don't know it tests the right thing. Small, reviewable steps, with decisions that are expensive to reverse written down as ADRs.

## Repository layout

```text
.claude-plugin/        plugin.json and marketplace.json
skills/<name>/SKILL.md one directory per skill
scripts/               release tooling
docs/adr/              architecture decision records
docs/superpowers/      design specs and implementation plans
```

The repo root is the plugin, and the marketplace in the same repo lists it ([ADR-0001](docs/adr/0001-ship-the-collection-as-one-root-plugin-superpowers-style.md)).

## Contributing

See [AGENTS.md](AGENTS.md) for how skills are structured, tested and released.

## Acknowledgements

Structure and release tooling follow [obra/superpowers](https://github.com/obra/superpowers) by Jesse Vincent.

## License

MIT, see [LICENSE](LICENSE).
````

- [ ] **Step 2: Write `AGENTS.md`**

````markdown
# agentic-engineering — contributor guide

This repo is a Claude Code plugin. The repo root is the plugin; `.claude-plugin/marketplace.json` lists it as the only entry (ADR-0001). Read this before changing anything.

## Layout

- `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`: manifests. Versions must match; never edit them by hand, use `scripts/bump-version.sh`.
- `skills/<skill-name>/SKILL.md`: one directory per skill, supporting files alongside `SKILL.md`.
- `docs/adr/`: decisions, managed with the `recording-decisions` skill (`adr.py`). Never edit an accepted ADR's body; supersede it.
- `docs/superpowers/specs/`, `docs/superpowers/plans/`: design specs and implementation plans.

## Writing a skill

Every `SKILL.md` starts with frontmatter:

```yaml
---
name: skill-name            # kebab-case, matches the directory name
description: Use when ...   # the trigger: when to load it, not what it does
---
```

Skills are code that shapes agent behaviour. Develop and test them with `superpowers:writing-skills`: watch an agent fail the scenario without the skill, add the skill, watch it pass, then pressure-test it. A skill without that evidence doesn't merge.

Third-party skills keep their original license and author credit in the skill directory and in the README table.

## Workflow

- Short-lived branches: `feat/`, `fix/`, `docs/`, `chore/`.
- Conventional commits: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`.
- One logical change per commit and per PR; fill in the PR template.

## Releasing

1. `scripts/bump-version.sh X.Y.Z`: bumps both manifests and audits for stray version strings.
2. Add an `X.Y.Z` entry at the top of `RELEASE-NOTES.md`.
3. `claude plugin validate --strict .`: must exit 0.
4. Commit as `chore: release X.Y.Z`, merge to `main`, then `claude plugin tag`.
````

- [ ] **Step 3: Write `CLAUDE.md`**

```markdown
@AGENTS.md
```

- [ ] **Step 4: Write `RELEASE-NOTES.md`**

```markdown
# Release Notes

## 0.1.0 — 2026-09-26

- Bootstrap the `agentic-engineering` plugin and marketplace (Claude Code).
- No skills yet. The previous copy-paste skill collection was removed; it remains in git history.
- Add `scripts/bump-version.sh` for keeping manifest versions in sync.
```

- [ ] **Step 5: Write `.github/PULL_REQUEST_TEMPLATE.md`**

```markdown
## What problem does this solve?
<!-- The concrete session, failure or gap that motivated this. "Improving" is not a problem statement. -->

## What does this change?
<!-- 1-3 sentences. -->

## Evidence
<!-- Skill changes: before/after behaviour from writing-skills pressure tests.
     Tooling changes: the commands you ran and their output. -->

## Environment tested

| Harness + version | Model | Plugins installed |
|-------------------|-------|-------------------|
|                   |       |                   |

## Checklist
- [ ] One logical change
- [ ] `claude plugin validate --strict .` passes
- [ ] `scripts/bump-version.sh --check` shows no drift
```

- [ ] **Step 6: Write `.github/ISSUE_TEMPLATE/bug_report.md`**

```markdown
---
name: Bug report
about: A skill or the plugin isn't behaving as expected
labels: bug
---

## Environment

| Field | Value |
|-------|-------|
| agentic-engineering version | |
| Harness + version | |
| Model | |
| Other plugins installed | |
| OS + shell | |

## What happened?

## Steps to reproduce
1.
2.
3.

## Expected behaviour

## Transcript or debug log
<!-- The single most useful thing you can attach. -->
```

- [ ] **Step 7: Write `.github/ISSUE_TEMPLATE/feature_request.md`**

```markdown
---
name: Feature request
about: Propose a new skill or a change to an existing one
labels: enhancement
---

## What problem does this solve?
<!-- From a real session: what were you doing, what went wrong or was missing? -->

## Proposed solution

## Alternatives considered

## Environment

| Field | Value |
|-------|-------|
| agentic-engineering version | |
| Harness + version | |
| Model | |
```

- [ ] **Step 8: Update `.gitignore` and write `.gitattributes`**

`.gitignore` (full content):
```
.DS_Store
__pycache__/
.idea/
.vscode/
.worktrees/
.claude/settings.local.json
```

`.gitattributes`:
```
*.sh text eol=lf
*.md text eol=lf
*.json text eol=lf
```

- [ ] **Step 9: Verify**

Run: `git check-ignore -v .claude-plugin/plugin.json .claude-plugin/marketplace.json skills/.gitkeep; echo "exit=$?"`
Expected: no output, `exit=1` (nothing ignored).

Run: `for l in LICENSE AGENTS.md docs/adr/0001-ship-the-collection-as-one-root-plugin-superpowers-style.md; do test -f "$l" && echo "ok $l"; done`
Expected: three `ok` lines (every relative README link resolves).

Run: `grep -rniE 'superpowers|jesse' .github CLAUDE.md RELEASE-NOTES.md; echo "exit=$?"`
Expected: `exit=1` (no leftover superpowers branding in templates).

Run: `claude plugin validate --strict . ; echo "exit=$?"` → `exit=0`
Run: `scripts/bump-version.sh --audit | tail -1` → `No undeclared files contain the version string. All clear.`

- [ ] **Step 10: Commit**

```bash
git add README.md AGENTS.md CLAUDE.md RELEASE-NOTES.md .gitignore .gitattributes .github
git commit -q -m "docs: add README, contributor guide, release notes and GitHub templates

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Final verification, then outward-facing steps (gated)

**Files:** none changed unless verification fails.

- [ ] **Step 1: Full verification, output shown to Michael**

```bash
git ls-files
claude plugin validate --strict . ; echo "validate-exit=$?"
scripts/bump-version.sh --check ; echo "check-exit=$?"
shellcheck scripts/bump-version.sh ; echo "shellcheck-exit=$?"
python3 ~/.claude/skills/recording-decisions/scripts/adr.py check
git status --short
```
Expected: tracked files match the spec's tree; all exits 0; ADR check passed; clean status.

- [ ] **Step 2: Whole-branch review**

Use `superpowers:requesting-code-review` against `main...feat/marketplace-bootstrap`.

- [ ] **Step 3: STOP — ask Michael before any of the following**

Present, and run only on explicit approval:
```bash
git switch main && git merge --ff-only feat/marketplace-bootstrap
git push origin main
gh repo rename agentic-engineering --repo MichaelD-42/agentic-skills --yes
git remote set-url origin https://github.com/MichaelD-42/agentic-engineering.git
git fetch origin && git status -sb
git branch -d feat/marketplace-bootstrap
```
Undo for the rename: `gh repo rename agentic-skills --repo MichaelD-42/agentic-engineering --yes` and reset the remote URL. Tell Michael to rename the local directory `~/workspace/agentic-skills` → `~/workspace/agentic-engineering` after this session ends.
