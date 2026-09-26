# agentic-engineering — contributor guide

This repo is a Claude Code plugin. The repo root is the plugin; `.claude-plugin/marketplace.json` lists it as the only entry (ADR-0001). Read this before changing anything.

## Layout

- `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`: manifests. Versions must match; never edit them by hand, use `scripts/bump-version.sh`.
- `skills/<skill-name>/SKILL.md`: one directory per skill, supporting files alongside `SKILL.md`.
- `docs/adr/`: decisions, managed with the `recording-decisions` skill (`adr.py`). Never edit an accepted ADR's body; supersede it.
- `docs/superpowers/specs/`, `docs/superpowers/plans/`: design specs and implementation plans.

## Superpowers dependency

This plugin requires [Superpowers](https://github.com/obra/superpowers) and is designed to work with it. Skills here extend the Superpowers workflow rather than replace it:

- Reference Superpowers skills by their namespaced name (`superpowers:brainstorming`, `superpowers:test-driven-development`, …) and hand off to them instead of duplicating their content.
- Don't add a skill that overlaps a Superpowers skill; extend or complement it.
- Follow Superpowers' conventions for skill structure and voice, so both plugins read as one workflow.

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
3. `claude plugin validate --strict .claude-plugin/marketplace.json && claude plugin validate --strict .claude-plugin/plugin.json`: both must exit 0 (validating `.` checks only the marketplace).
4. Commit as `chore: release X.Y.Z`, merge to `main`, then `claude plugin tag`.
