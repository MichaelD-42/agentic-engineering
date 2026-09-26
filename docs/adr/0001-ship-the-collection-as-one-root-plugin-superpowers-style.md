---
status: accepted
date: 2026-09-26
decision-makers: Michael Dold
review-by: 2027-09-26
---

# Ship the collection as one root plugin, superpowers-style

> In the context of turning this repo into a Claude Code marketplace for agentic-engineering skills, facing the choice between one plugin and many, we decided for a single plugin at the repo root to achieve one install that delivers every skill, accepting that splitting into several plugins later means restructuring the repo and changing the install command.

## Context and Problem Statement

The repo is being rebuilt as a Claude Code marketplace, modelled on obra/superpowers, and skills will be added over time. A marketplace can list one plugin whose source is the repo root, or many plugins under `plugins/<name>/`. Which shape should every future skill fit into?

## Considered Options

* Single root plugin (`marketplace.json` → `"source": "./"`, `skills/` at root) — good: mirrors superpowers exactly, one install gets everything, simplest layout; bad: users can't install a subset, and a second plugin forces a restructure.
* Multi-plugin marketplace (`plugins/<name>/.claude-plugin/plugin.json`) — good: plugins can be installed and versioned independently; bad: extra nesting and per-plugin manifests to maintain for what is currently one coherent collection.

## Decision Outcome

Chosen option: "Single root plugin", because the skills form one agentic-engineering workflow meant to be installed together, and superpowers proves the shape works.

### Consequences

* Good, because installation is one command (`/plugin install agentic-engineering@agentic-engineering`) and there is one version to bump.
* Good, because skills can reference each other as `agentic-engineering:<skill>` without cross-plugin dependencies.
* Bad, because every skill loads its description into context for every user, even skills they never use.
* Bad, because moving to multi-plugin later changes the install id and moves `skills/`, breaking existing installs.

### Confirmation

`claude plugin validate --strict .` passes with the marketplace entry's `source` set to `./`.
