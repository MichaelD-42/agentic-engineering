#!/usr/bin/env python3
"""SessionStart hook: warn when Superpowers or its visual companion is missing."""

from pathlib import Path

COMPANION = Path("skills/brainstorming/scripts/start-server.sh")

MISSING_USER = (
    "agentic-engineering: Superpowers isn't installed or enabled, so hand-offs to "
    "superpowers:* skills won't work. Install it with "
    "/plugin install superpowers@claude-plugins-official"
)
MISSING_MODEL = (
    "Superpowers is not available in this session. Do not invoke superpowers:* skills. "
    "When an agentic-engineering skill says to hand off to one, tell the user "
    "Superpowers is missing and stop at that step."
)
NO_COMPANION_USER = (
    "agentic-engineering: Superpowers' visual companion "
    "(skills/brainstorming/scripts/start-server.sh) wasn't found; eliciting-needs "
    "will use its static canvas page instead."
)


def problems(plugins: list) -> tuple[str, str | None] | None:
    """(user message, model context) for what's wrong, or None if healthy."""
    enabled = [
        p
        for p in plugins
        if isinstance(p, dict)
        and str(p.get("id", "")).startswith("superpowers@")
        and p.get("enabled") is True
    ]
    if not enabled:
        return MISSING_USER, MISSING_MODEL
    if not any(p.get("installPath") and (Path(p["installPath"]) / COMPANION).is_file() for p in enabled):
        return NO_COMPANION_USER, None
    return None
