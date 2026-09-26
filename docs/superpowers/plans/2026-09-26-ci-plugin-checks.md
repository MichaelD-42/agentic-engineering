# CI Plugin Checks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A GitHub Actions workflow that runs the repo's four credential-free checks on every PR and push to `main`.

**Architecture:** One workflow file, one job. Setup steps, then four named check steps; every check after the first runs with `if: ${{ !cancelled() }}` so one failure doesn't hide the others. Proof that each check can fail comes from a throwaway draft PR, so no junk commits reach `ci/plugin-checks`.

**Tech Stack:** GitHub Actions, `uv` + pytest, npm (`@anthropic-ai/claude-code@stable`), bash + `jq`.

**Spec:** `docs/superpowers/specs/2026-09-26-ci-plugin-checks-design.md`

## Global Constraints

- No secrets and no API key; `permissions: contents: read`.
- Triggers: `pull_request`, and `push` to `main`.
- Claude Code from the `stable` npm dist-tag, unpinned.
- Third-party actions pinned to a commit SHA, tag in a trailing comment.
- Checks: `claude plugin validate --strict` on both manifests, `uv run pytest`, `adr.py check`, `bump-version.sh --check`. Not `--audit`, not scenarios, not `plugin eval`.
- Every push to GitHub, and opening any PR, is confirmed with Michael first.

## Review Focus

- The `claude` install step fails (npm outage, tag missing): later steps still run under `!cancelled()`, and pytest, ADR and version checks must still report their own result. Covered by reading the run logs in Task 2.
- A check fails: the steps after it must still run and report. Covered by each injection in Task 2 (the validate injection is the first step, so all three later steps must show green).
- `uv run pytest` on the runner resolves Python ≥ 3.12 from `requires-python`; a wrong interpreter would fail at import. Covered by the green run in Task 2.
- A PR from a fork: the workflow uses no secrets, so it must run identically. Not testable here without a fork; the `permissions`/no-secrets constraint is what guarantees it.
- `claude` on a fresh runner prompts or needs a login for `plugin validate`: verified locally with an empty `HOME`; the green run in Task 2 confirms it on the runner.

---

### Task 1: Workflow and AGENTS.md note

**Files:**
- Create: `.github/workflows/checks.yml`
- Modify: `AGENTS.md:45`

**Interfaces:**
- Produces: workflow `checks`, job `checks`, steps named `Validate manifests`, `Unit tests`, `ADRs`, `Version sync`. Task 2 reads results by these names.

- [ ] **Step 1: Confirm each check fails on a broken repo (the "failing test")**

Already run against a scratch clone before writing this plan; rerun if anything changed:

```bash
S=$(mktemp -d) && git clone -q . "$S" && cd "$S"
jq '.bogusField="x"' .claude-plugin/plugin.json > x && mv x .claude-plugin/plugin.json
claude plugin validate --strict .claude-plugin/plugin.json; echo "exit=$?"   # expect 1
git checkout -q .
sed -i 's/^status: accepted/status: bogus/' docs/adr/0003-*.md
python3 skills/recording-decisions/scripts/adr.py check; echo "exit=$?"       # expect 1
git checkout -q .
jq '.plugins[0].version="0.1.1"' .claude-plugin/marketplace.json > x && mv x .claude-plugin/marketplace.json
scripts/bump-version.sh --check; echo "exit=$?"                                # expect 1
cd - && rm -rf "$S"
```

Expected: every `exit=1`. (pytest failing on a failing test needs no proof.)

- [ ] **Step 2: Write the workflow**

`.github/workflows/checks.yml`:

```yaml
name: checks

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: astral-sh/setup-uv@c18668ad3cf93ea998bef934396af7bb5c839dc7 # v10.2.0
      - uses: actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0
        with:
          node-version: lts/*
      - name: Install Claude Code
        run: npm install -g @anthropic-ai/claude-code@stable

      - name: Validate manifests
        run: |
          claude plugin validate --strict .claude-plugin/marketplace.json
          claude plugin validate --strict .claude-plugin/plugin.json
      - name: Unit tests
        if: ${{ !cancelled() }}
        run: uv run pytest
      - name: ADRs
        if: ${{ !cancelled() }}
        run: python3 skills/recording-decisions/scripts/adr.py check
      - name: Version sync
        if: ${{ !cancelled() }}
        run: scripts/bump-version.sh --check
```

- [ ] **Step 3: Lint the workflow**

Run: `uvx --from actionlint-py actionlint .github/workflows/checks.yml`
Expected: no output, exit 0.

- [ ] **Step 4: Note CI in AGENTS.md**

Replace line 45 of `AGENTS.md`:

```markdown
3. `claude plugin validate --strict .claude-plugin/marketplace.json && claude plugin validate --strict .claude-plugin/plugin.json`: both must exit 0 (validating `.` checks only the marketplace). CI (`.github/workflows/checks.yml`) runs these, `pytest`, `adr.py check` and `bump-version.sh --check` on every PR.
```

- [ ] **Step 5: Run the four checks locally on the branch**

```bash
claude plugin validate --strict .claude-plugin/marketplace.json && claude plugin validate --strict .claude-plugin/plugin.json
uv run pytest -q
python3 skills/recording-decisions/scripts/adr.py check
scripts/bump-version.sh --check
```

Expected: all exit 0 (95 tests pass).

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/checks.yml AGENTS.md
git commit -m "ci: run plugin checks on every PR"
```

### Task 2: Prove red and green on GitHub

**Files:** none on `ci/plugin-checks`. Throwaway branch `ci/plugin-checks-failproof`, deleted at the end.

**Interfaces:**
- Consumes: the step names from Task 1.

Every `git push` and `gh pr create` in this task needs Michael's go-ahead first; ask once for the whole task.

- [ ] **Step 1: Throwaway branch and draft PR**

```bash
git switch -c ci/plugin-checks-failproof
git push -u origin ci/plugin-checks-failproof
gh pr create --draft --base main --title "DO NOT MERGE: CI failure proof" --body "Throwaway: proves each check in checks.yml can fail. Closed and deleted after."
```

- [ ] **Step 2: One injection per failure class**

For each row: apply, commit `test: break <check>`, push, wait with `gh run watch --exit-status` (expect non-zero), then record step outcomes with `gh run view --json jobs --jq '.jobs[0].steps[] | "\(.name): \(.conclusion)"'`, then `git revert --no-edit HEAD` and continue.

| Check | Injection | Expected |
|---|---|---|
| Validate manifests | `jq '.bogusField="x"' .claude-plugin/plugin.json > x && mv x .claude-plugin/plugin.json` | Validate manifests: failure; Unit tests, ADRs, Version sync: success |
| Unit tests | append `def test_ci_red():\n    assert False` to `tests/eliciting-needs/test_canvas.py` | Unit tests: failure; others success |
| ADRs | `sed -i 's/^status: accepted/status: bogus/' docs/adr/0003-*.md` | ADRs: failure; others success |
| Version sync | `jq '.plugins[0].version="0.1.1"' .claude-plugin/marketplace.json > x && mv x .claude-plugin/marketplace.json` | Version sync: failure; others success |

- [ ] **Step 3: Green on the final revert**

Push after the last revert; `gh run watch --exit-status` exits 0 and every step shows `success`.

- [ ] **Step 4: Clean up**

```bash
gh pr close --delete-branch ci/plugin-checks-failproof
git switch ci/plugin-checks
git branch -D ci/plugin-checks-failproof
```

Keep the four red run URLs and the green one for the real PR's Evidence section.

### Task 3: Open the real PR

- [ ] **Step 1: Push and open**

```bash
git push -u origin ci/plugin-checks
gh pr create --base main --title "ci: run plugin checks on every PR" --body-file <filled PULL_REQUEST_TEMPLATE.md>
```

Evidence section: the four red run links with the failing step each, the green run, local check output from Task 1 Step 5. Environment: Claude Code version from the runner log.

- [ ] **Step 2: Confirm the PR's own run is green**

Run: `gh pr checks --watch`
Expected: `checks` passes.

Merging and branch protection are Michael's call.
