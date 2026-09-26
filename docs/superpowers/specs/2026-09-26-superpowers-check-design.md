# Superpowers check — design

Date: 2026-09-26
Status: approved in brainstorming, pending spec review

## Goal

Warn at session start when Superpowers is missing or its visual companion can't be found. This resolves the unenforced requirement accepted in ADR-0002 and makes ADR-0003's companion dependency visible instead of silently degrading.

Done means: a session without an enabled Superpowers shows the warning to the user and tells the model not to hand off; a session with Superpowers whose companion script is gone shows a one-line notice; a healthy session outputs nothing.

## Decisions

- **Ask the CLI, don't parse settings.** `claude plugin list --json` returns every plugin's `id`, `enabled` and `installPath` with settings precedence already resolved (~130 ms). Reading `installed_plugins.json` and the settings layers ourselves would copy undocumented rules. Globbing the plugin cache is wrong outright: the cache keeps stale versions and disabled plugins.
- **Fail open.** If `claude` isn't on PATH, exits non-zero, takes over 5 s, or prints something that isn't a JSON list, the hook prints nothing and exits 0. A false "Superpowers missing" is worse than a missed one.
- **Both audiences for a missing Superpowers**, user only for a missing companion: `eliciting-needs` already falls back to a static page, so the model needs no instruction.
- **Fires on `startup|clear|compact`**, like Superpowers' own hook, because the model's context resets on clear and compact. The user line repeats on those events; acceptable, since it only appears in a broken setup.
- Stdlib Python 3, like the plugin's other scripts.
- No ADR: cheap to reverse, nothing else conforms to it.

Out of this branch: exporting the resolved Superpowers path via `CLAUDE_ENV_FILE` so `eliciting-needs` stops globbing the cache. That changes ADR-0003's approach and gets its own branch.

## Change

`hooks/hooks.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|clear|compact",
        "hooks": [
          { "type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/session_check.py\"" }
        ]
      }
    ]
  }
}
```

`hooks/session_check.py`:

- `problems(plugins: list[dict]) -> tuple[str, str | None] | None` — pure. Returns `(user_message, model_context)` or `None` when healthy.
  1. No entry whose `id` starts with `superpowers@` and has `enabled` true →
     - user: `agentic-engineering: Superpowers isn't installed or enabled, so hand-offs to superpowers:* skills won't work. Install it with /plugin install superpowers@claude-plugins-official`
     - model: `Superpowers is not available in this session. Do not invoke superpowers:* skills. When an agentic-engineering skill says to hand off to one, tell the user Superpowers is missing and stop at that step.`
  2. Otherwise, no enabled Superpowers entry has `<installPath>/skills/brainstorming/scripts/start-server.sh` →
     - user: `agentic-engineering: Superpowers' visual companion (skills/brainstorming/scripts/start-server.sh) wasn't found; eliciting-needs will use its static canvas page instead.`
     - model: `None`
- `main()` runs `claude plugin list --json` (5 s timeout), passes the parsed list to `problems()`, and on a problem prints `{"systemMessage": user, "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": model}}`, omitting `hookSpecificOutput` when `model` is `None`. Always exits 0.

README: one sentence under Requirements that the plugin warns at session start when Superpowers is missing.

## Known gap

When Superpowers is loaded with `--plugin-dir` rather than installed, `claude plugin list` doesn't show it and the hook warns wrongly. Developer-only setup; accepted.

## Verification

- `tests/hooks/test_session_check.py`:
  - `problems()`: healthy → `None`; no Superpowers → both messages; Superpowers present but `enabled: false` → both messages; enabled with companion missing (temp `installPath` without the script) → user message only; two entries, one disabled and one healthy → `None`.
  - `main()` end to end with a fake `claude` script first on PATH: healthy list → no output; empty list → valid JSON with both fields; `claude` absent from PATH → no output, exit 0; non-JSON output → no output, exit 0; non-zero exit → no output, exit 0.
- Real CLI: run the hook with `CLAUDE_CONFIG_DIR` set to an empty temp dir → warning JSON; with the real config → no output.
- `claude plugin validate --strict` on both manifests still passes with `hooks/hooks.json` present; CI green on the PR.

## Out of scope

Version floors for Superpowers, other harnesses' hook formats, the `CLAUDE_ENV_FILE` path export.
