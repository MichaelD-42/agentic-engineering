# agentic-engineering

A Claude Code plugin of skills for agentic engineering: getting coding agents to work the way a disciplined engineer does. Design before code, a failing test before the fix, evidence before any claim of "done".

Skills are instruction sets that Claude Code loads when their trigger matches the task in front of it. This plugin bundles them so one install gives you the whole workflow.

## Requirements

This plugin depends on [Superpowers](https://github.com/obra/superpowers). Its skills are designed to run alongside the Superpowers workflow (brainstorming, planning, TDD, debugging, verification) and hand off to Superpowers skills by name, so without it they are incomplete. Install Superpowers first:

```text
/plugin install superpowers@claude-plugins-official
```

## Installation

```text
/plugin marketplace add MichaelD-42/agentic-engineering
/plugin install agentic-engineering@agentic-engineering
```

To update: `/plugin marketplace update agentic-engineering`.

## Skills

| Skill | Use when |
|-------|----------|
| `eliciting-needs` | Someone brings a first idea for an AI use case, tool, bot, agent or automation, before any solution is designed. Turns the idea into a need canvas, roasts it, and only then sketches the least-AI solution that meets it (often a script, sometimes "don't build"). |
| `recording-decisions` | Choosing between approaches, libraries, data models or architectural patterns, or recording, superseding or reviewing a decision. Gates which decisions get an ADR, writes MADR 4.0 records with `adr.py`, and blocks edits to decided ADRs. |

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
