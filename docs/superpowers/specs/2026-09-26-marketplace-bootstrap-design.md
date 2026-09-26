# Marketplace bootstrap — design

Date: 2026-09-26
Status: approved in brainstorming, pending spec review

## Goal

Replace the loose copy-paste skill collection in `MichaelD-42/agentic-skills` with a Claude Code plugin and marketplace for agentic engineering, modelled on [obra/superpowers](https://github.com/obra/superpowers). The bootstrap ships no skills; skills are added in later changes.

Done means: the repo validates as a plugin and marketplace, installs with two commands, has release tooling that keeps versions in sync, and documents how to add a skill.

## Decisions

- **Layout:** one plugin at the repo root, listed by a marketplace in the same repo. See ADR-0001.
- **Harnesses:** Claude Code only. Other harness manifests (Codex, Cursor, Gemini, …) are added when actually used.
- **Names:** plugin, marketplace, GitHub repo, and local directory are all `agentic-engineering`. Install id: `agentic-engineering@agentic-engineering`.
- **Bootstrap hook:** deferred. The SessionStart hook and the `using-agentic-engineering` skill it injects are written together with the first real skills, since until then they have nothing to route to.
- **Manifests carry the author's name only**, no email.

## Repo after the change

```
.claude-plugin/
  marketplace.json          marketplace "agentic-engineering", owner Michael Dold,
                            plugins[0]: name agentic-engineering, source "./", version 0.1.0
  plugin.json               name, description, version 0.1.0, author, homepage,
                            repository (github.com/MichaelD-42/agentic-engineering), license MIT, keywords
skills/.gitkeep             skills live at skills/<name>/SKILL.md
scripts/bump-version.sh     ported from superpowers (MIT, credited in header), JSON fields only
.version-bump.json          declares .claude-plugin/plugin.json#version and
                            .claude-plugin/marketplace.json#plugins.0.version
.github/
  ISSUE_TEMPLATE/bug_report.md
  ISSUE_TEMPLATE/feature_request.md
  PULL_REQUEST_TEMPLATE.md  problem, change, eval evidence, environment tested
docs/adr/                   ADRs, managed with adr.py
docs/superpowers/specs/     design specs
AGENTS.md                   contributor guide (see below)
CLAUDE.md                   single line: @AGENTS.md
README.md
RELEASE-NOTES.md            starts with 0.1.0
LICENSE                     unchanged (MIT, © 2026 Michael Dold)
.gitignore, .gitattributes  current ignores + superpowers' LF rules
```

Removed: all nine skills under `skills/` and the current generic `AGENTS.md` template. Both remain in git history.

## Content

**README.md** covers what the plugin is and who it's for (agentic engineering: disciplined, test-first, evidence-based work with coding agents), installation, a skills table that says there are none yet, the repo layout, how to add a skill, how to release, and the license.

**AGENTS.md** is a contributor guide for humans and agents. It is much shorter than superpowers' version, which is written to defend a heavily trafficked public repo. It covers:
- where skills live and the `SKILL.md` frontmatter (`name`, a `description` that starts "Use when…")
- that skill changes are tested with `superpowers:writing-skills` before merging
- conventional commits and short-lived feature branches
- the release steps: bump the version, add release notes, run `claude plugin validate --strict .`

**bump-version.sh** keeps superpowers' interface: `<version>` bumps, `--check` reports drift, and `--audit` greps for stale version strings. The YAML support is dropped because no YAML manifests exist.

## Verification

- `claude plugin validate --strict .` passes.
- `scripts/bump-version.sh --check` shows 0.1.0 in both manifests, with no drift.
- `shellcheck scripts/bump-version.sh` is clean.
- `bump-version.sh 0.1.1`, run on a scratch copy of the repo, rewrites both manifests.
- No local install test, because it would change the user's `~/.claude` plugin state.

## Rename (outward-facing, confirmed before running)

After the branch is merged and pushed: `gh repo rename agentic-engineering`, then `git remote set-url origin https://github.com/MichaelD-42/agentic-engineering.git`. The local directory is renamed by hand after the session. Undo: `gh repo rename agentic-skills`. GitHub redirects the old URL in the meantime.

## Out of scope

Skills, hooks, the bootstrap skill, evals, other harnesses, CI.
