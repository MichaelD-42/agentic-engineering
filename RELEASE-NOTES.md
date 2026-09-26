# Release Notes

## Unreleased

- Add the `evaluating-ai-features` skill: eval set before prompt, `evalset.py` (new, check, status) with a gate of 20+ distinct inputs, half real, a refusal case and every success criterion covered. `eliciting-needs` now hands runtime-AI outcomes to it before brainstorming.
- Add a SessionStart hook that warns when Superpowers is missing or disabled, or its visual companion can't be found (resolves the unenforced requirement in ADR-0002).
- Add CI: every PR runs strict manifest validation, pytest, `adr.py check` and `bump-version.sh --check`.
- Add the `eliciting-needs` skill: need canvas (`canvas.py`), plain-language probes, AI-fit classification and roast rubric, with an optional live view through the Superpowers visual companion (ADR-0003).
- Add the `recording-decisions` skill: ADR gate, `adr.py` CLI (new, accept, supersede, check, stale, index), MADR 4.0 templates, and hooks that block edits to decided ADRs and validate every ADR write.

## 0.1.0 — 2026-09-26

- Bootstrap the `agentic-engineering` plugin and marketplace (Claude Code).
- No skills yet. The previous copy-paste skill collection was removed; it remains in git history.
- Add `scripts/bump-version.sh` for keeping manifest versions in sync.
- Requires [Superpowers](https://github.com/obra/superpowers); skills are designed to work with it.
