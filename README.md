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
