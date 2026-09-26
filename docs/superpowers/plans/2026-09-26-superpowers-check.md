# Superpowers Check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A SessionStart hook that warns when Superpowers isn't enabled or its visual companion is missing, and says nothing otherwise.

**Architecture:** `hooks/hooks.json` runs `hooks/session_check.py`. A pure `problems()` decides what's wrong from the plugin list; `main()` gets that list from `claude plugin list --json`, fails open on any error, and prints the hook JSON.

**Tech Stack:** Python 3.12 stdlib, pytest (via `uv run`), Claude Code plugin hooks.

**Spec:** `docs/superpowers/specs/2026-09-26-superpowers-check-design.md`

## Global Constraints

- Stdlib only; the hook always exits 0.
- Fail open: `claude` missing, non-zero exit, >5 s, or output that isn't a JSON list → no output.
- Matcher `startup|clear|compact`.
- Messages verbatim from the spec (copied into Task 1).
- Missing companion → `systemMessage` only, no `hookSpecificOutput`.

## Review Focus

- `claude plugin list` hangs: the 5 s timeout must turn it into silence. Not unit-tested (a real timeout test costs 5 s per run); the reviewer checks `TimeoutExpired` is caught.
- The CLI's JSON changes shape (a dict, or entries that aren't dicts): must stay silent or treat as missing, never crash. Covered by `test_non_list_json_is_silent` and `test_non_dict_entries_ignored` in Tasks 1–2.
- `installPath` missing or empty on an entry: must count as "companion missing", not resolve relative to the session's cwd. Covered by `test_empty_install_path_is_missing_companion` in Task 1.
- Hook runs with a PATH that lacks `claude` (e.g. a native install in `~/.local/bin` not exported to hooks): silent. Covered by `test_claude_absent_is_silent` in Task 2.
- `claude plugin list` with an empty config dir might prompt or print onboarding text instead of JSON: covered by the real-CLI check in Task 2 Step 6.

---

### Task 1: `problems()` decides what's wrong

**Files:**
- Create: `hooks/session_check.py`
- Test: `tests/hooks/test_session_check.py`

**Interfaces:**
- Produces: `problems(plugins: list) -> tuple[str, str | None] | None`; constants `MISSING_USER`, `MISSING_MODEL`, `NO_COMPANION_USER`, `COMPANION`.

- [ ] **Step 1: Write the failing tests**

`tests/hooks/test_session_check.py`:

```python
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parent.parent.parent / "hooks"
sys.path.insert(0, str(HOOKS))
import session_check as sc  # noqa: E402


def superpowers(install_path, enabled=True, marketplace="claude-plugins-official"):
    return {
        "id": f"superpowers@{marketplace}",
        "enabled": enabled,
        "installPath": str(install_path),
    }


class ProblemsTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.healthy = Path(tmp.name) / "healthy"
        (self.healthy / sc.COMPANION).parent.mkdir(parents=True)
        (self.healthy / sc.COMPANION).write_text("#!/bin/sh\n")
        self.broken = Path(tmp.name) / "broken"
        self.broken.mkdir()

    def test_healthy_is_none(self):
        self.assertIsNone(sc.problems([superpowers(self.healthy)]))

    def test_any_marketplace_counts(self):
        self.assertIsNone(sc.problems([superpowers(self.healthy, marketplace="superpowers-marketplace")]))

    def test_missing_warns_both(self):
        self.assertEqual(sc.problems([]), (sc.MISSING_USER, sc.MISSING_MODEL))

    def test_disabled_warns_both(self):
        self.assertEqual(
            sc.problems([superpowers(self.healthy, enabled=False)]),
            (sc.MISSING_USER, sc.MISSING_MODEL),
        )

    def test_missing_companion_warns_user_only(self):
        self.assertEqual(sc.problems([superpowers(self.broken)]), (sc.NO_COMPANION_USER, None))

    def test_empty_install_path_is_missing_companion(self):
        entry = superpowers(self.healthy)
        entry["installPath"] = ""
        self.assertEqual(sc.problems([entry]), (sc.NO_COMPANION_USER, None))

    def test_one_disabled_one_healthy_is_none(self):
        self.assertIsNone(
            sc.problems([superpowers(self.broken, enabled=False), superpowers(self.healthy)])
        )

    def test_non_dict_entries_ignored(self):
        self.assertIsNone(sc.problems(["junk", 3, superpowers(self.healthy)]))
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/hooks -q`
Expected: collection error, `ModuleNotFoundError: No module named 'session_check'`.

- [ ] **Step 3: Write `problems()`**

`hooks/session_check.py`:

```python
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
```

- [ ] **Step 4: Run to verify they pass**

Run: `uv run pytest tests/hooks -q`
Expected: `8 passed`.

- [ ] **Step 5: Commit**

```bash
git add hooks/session_check.py tests/hooks/test_session_check.py
git commit -m "feat: detect missing Superpowers and companion"
```

### Task 2: Hook entry point, registration, README

**Files:**
- Modify: `hooks/session_check.py` (add `plugin_list()`, `main()`)
- Create: `hooks/hooks.json`
- Modify: `README.md:9` (Requirements)
- Test: `tests/hooks/test_session_check.py` (add `MainTests`)

**Interfaces:**
- Consumes: `problems()`, `MISSING_USER`, `MISSING_MODEL`, `NO_COMPANION_USER`, `COMPANION` from Task 1.

- [ ] **Step 1: Write the failing end-to-end tests**

Append to `tests/hooks/test_session_check.py` (add `import json`, `import os`, `import subprocess` to the imports at the top):

```python
class MainTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.bin = Path(tmp.name) / "bin"
        self.bin.mkdir()
        self.healthy = Path(tmp.name) / "sp"
        (self.healthy / sc.COMPANION).parent.mkdir(parents=True)
        (self.healthy / sc.COMPANION).write_text("#!/bin/sh\n")

    def fake_claude(self, stdout, code=0):
        out = self.bin / "out.txt"
        out.write_text(stdout)
        script = self.bin / "claude"
        script.write_text(f"#!/bin/sh\ncat '{out}'\nexit {code}\n")
        script.chmod(0o755)

    def run_hook(self):
        result = subprocess.run(
            [sys.executable, str(HOOKS / "session_check.py")],
            capture_output=True,
            text=True,
            env={**os.environ, "PATH": str(self.bin)},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_healthy_prints_nothing(self):
        self.fake_claude(json.dumps([superpowers(self.healthy)]))
        self.assertEqual(self.run_hook(), "")

    def test_missing_prints_both_fields(self):
        self.fake_claude("[]")
        out = json.loads(self.run_hook())
        self.assertEqual(out["systemMessage"], sc.MISSING_USER)
        self.assertEqual(
            out["hookSpecificOutput"],
            {"hookEventName": "SessionStart", "additionalContext": sc.MISSING_MODEL},
        )

    def test_missing_companion_prints_user_only(self):
        self.fake_claude(json.dumps([superpowers(self.bin)]))
        out = json.loads(self.run_hook())
        self.assertEqual(out, {"systemMessage": sc.NO_COMPANION_USER})

    def test_claude_absent_is_silent(self):
        self.assertEqual(self.run_hook(), "")

    def test_bad_json_is_silent(self):
        self.fake_claude("Welcome to Claude Code!")
        self.assertEqual(self.run_hook(), "")

    def test_non_list_json_is_silent(self):
        self.fake_claude('{"plugins": []}')
        self.assertEqual(self.run_hook(), "")

    def test_nonzero_exit_is_silent(self):
        self.fake_claude("[]", code=1)
        self.assertEqual(self.run_hook(), "")
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/hooks -q`
Expected: `test_missing_prints_both_fields` and `test_missing_companion_prints_user_only` FAIL with `JSONDecodeError` (the script has no `main` and prints nothing). The five silence tests pass vacuously for the same reason; they become meaningful once `main()` exists. Task 1's 8 tests pass.

- [ ] **Step 3: Add `plugin_list()` and `main()`**

Add `import json`, `import subprocess`, `import sys` to the imports of `hooks/session_check.py`, then append:

```python
def plugin_list() -> list | None:
    """`claude plugin list --json`, or None if it can't be had."""
    try:
        result = subprocess.run(
            ["claude", "plugin", "list", "--json"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        plugins = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    return plugins if isinstance(plugins, list) else None


def main() -> int:
    plugins = plugin_list()
    found = problems(plugins) if plugins is not None else None
    if found:
        user, model = found
        output = {"systemMessage": user}
        if model:
            output["hookSpecificOutput"] = {
                "hookEventName": "SessionStart",
                "additionalContext": model,
            }
        print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run to verify they pass**

Run: `uv run pytest tests/hooks -q`
Expected: `15 passed`.

- [ ] **Step 5: Register the hook and note it in the README**

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

`README.md`, Requirements: add a new paragraph directly after the `/plugin install superpowers@…` code block:

```markdown
If Superpowers is missing or disabled, the plugin says so at session start.
```

- [ ] **Step 6: Check against the real CLI and validator**

```bash
T=$(mktemp -d) && CLAUDE_CONFIG_DIR="$T" python3 hooks/session_check.py; echo "exit=$?"; rm -r "$T"
python3 hooks/session_check.py; echo "exit=$?"
claude plugin validate --strict .claude-plugin/plugin.json && claude plugin validate --strict .claude-plugin/marketplace.json
uv run pytest -q
```

Expected: first run prints the missing-Superpowers JSON, `exit=0`; second prints nothing, `exit=0`; both validations pass; full suite `110 passed`.

- [ ] **Step 7: Commit**

```bash
git add hooks/hooks.json hooks/session_check.py tests/hooks/test_session_check.py README.md
git commit -m "feat: warn at session start when Superpowers is missing"
```
