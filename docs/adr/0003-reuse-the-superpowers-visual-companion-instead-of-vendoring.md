---
status: accepted
date: 2026-09-26
decision-makers: Michael
review-by: 2027-09-26
---

# Reuse the superpowers visual companion instead of vendoring it

> In the context of eliciting-needs showing the canvas live while the driver talks, facing a choice between depending on superpowers' companion server and copying it into this plugin, we decided to reuse the installed superpowers companion to avoid maintaining ~1.4k lines of server code, accepting that the skill breaks if superpowers changes the companion's location or interface.

## Context and Problem Statement

eliciting-needs shows the need canvas live in a browser while the driver talks, and `canvas.py render` produces the pages. superpowers ships a companion server (`skills/brainstorming/scripts/`: server.cjs, helper.js, frame template, start/stop scripts, ~1.4k lines) that serves the newest HTML file in a screen directory. The skill already hands off to superpowers:brainstorming, and the plugin requires Superpowers anyway (ADR-0002). The question is whether to use its server in place or copy it into this plugin.

## Considered Options

* Reuse in place (find the newest `~/.claude/plugins/cache/*/superpowers/*/skills/brainstorming/scripts/start-server.sh`) — good: no code to maintain, picks up upstream fixes; bad: depends on another plugin's internal path layout and CLI flags.
* Vendor the companion into this plugin — good: self-contained, pinned behaviour; bad: ~1.4k lines of Node server to maintain and keep secure, and they drift from upstream.

## Decision Outcome

Chosen option: "Reuse in place", because superpowers is already a hard dependency for the hand-off, and a static-HTML fallback (`canvas.py render` + `xdg-open`) covers the case where it's missing.

### Consequences

* Good, because this plugin stays stdlib Python plus templates, with no server code.
* Bad, because a superpowers release that moves `start-server.sh`, renames `--project-dir`/`--open`, or stops serving the newest file in `screen_dir` silently degrades the skill to the static fallback.
* Bad, because the discovery glob reads the plugin cache layout (`~/.claude/plugins/cache/<marketplace>/superpowers/<version>/…`), which Claude Code doesn't document as stable.

### Confirmation

Re-check the companion loop in a real session after each superpowers upgrade. Revisit if this plugin is published to a marketplace where superpowers may not be installed.
