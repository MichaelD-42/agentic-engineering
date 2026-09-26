# CI plugin checks — design

Date: 2026-09-26
Status: approved in brainstorming, pending spec review

## Goal

Enforce the PR template's checklist by machine instead of by trust. Every pull request, and every push to `main`, runs the repo's checks on GitHub Actions and goes red when one fails.

Done means: a clean PR goes green in about a minute, and a PR with a broken manifest, a failing test, an invalid ADR or version drift goes red on the matching step while the other steps still report.

## Decisions

- **No API key in CI.** Only checks that run without credentials. The `tests/*/scenarios/run.sh` pressure scenarios and `claude plugin eval` stay manual.
- **Four checks:** manifest validation, unit tests, ADR check, version sync. `bump-version.sh --audit` is left out; it's a release-time check and noisy on ordinary PRs.
- **Claude Code from the `stable` npm dist-tag**, unpinned. Manifests are validated against what most users run; an upstream validator change can turn `main` red without a commit here, which is the signal we want.
- **One workflow, one job, four steps.** Parallel jobs would multiply setup time for a suite that runs in seconds; a shared `scripts/check.sh` would duplicate commands `AGENTS.md` already lists.
- No ADR: cheap to reverse and nothing else conforms to it.

Verified before writing: `claude plugin validate --strict` passes on both manifests with an empty `HOME` and no credentials (2.1.283).

## Change

`.github/workflows/checks.yml`:

- Triggers: `pull_request`, and `push` to `main`.
- `runs-on: ubuntu-latest`, `permissions: contents: read`, no secrets.
- Setup: `actions/checkout`, `astral-sh/setup-uv`, `actions/setup-node`, then `npm install -g @anthropic-ai/claude-code@stable`. Third-party actions are pinned to a commit SHA with the tag in a trailing comment.
- Steps, each named so the PR shows which check failed; every check step after the first carries `if: ${{ !cancelled() }}` so one failure doesn't hide the others:
  1. **Validate manifests:** `claude plugin validate --strict .claude-plugin/marketplace.json` and `… .claude-plugin/plugin.json`.
  2. **Unit tests:** `uv run pytest`.
  3. **ADRs:** `python3 skills/recording-decisions/scripts/adr.py check`.
  4. **Version sync:** `scripts/bump-version.sh --check` (`jq` is preinstalled on the runner).

`AGENTS.md`, Releasing step 3: add that CI runs these checks on every PR. The PR template stays as is; contributors still run the checks before pushing.

## Verification

- Locally, before pushing: `actionlint` on the workflow, if available; otherwise a YAML parse.
- On the branch, one throwaway commit per failure class, each pushed and then reverted: an invalid field in `plugin.json`, a failing assertion in a test, broken ADR front matter, a version mismatch between the two manifests. Each must turn its own step red while the remaining steps still run.
- After the reverts: a green run on the final commit, linked in the PR.
- Pushing to the GitHub remote is outward-facing; confirmed with Michael before the first push.

## Out of scope

Scenario runs and `plugin eval` (need an API key), branch protection (a repo setting Michael makes), Dependabot for the pinned actions, other operating systems or Python versions.
