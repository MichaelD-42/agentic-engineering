# recording-decisions Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A superpowers-style skill that decides which decisions earn an ADR and writes, validates, supersedes and reviews them in MADR 4.0 form, with hooks that load only when the skill is invoked.

**Architecture:** One stdlib-only CLI (`scripts/adr.py`) owns all ADR mechanics: directory detection, numbering, templating, index, lifecycle, check, stale, digest. Two thin hook scripts import it. `SKILL.md` carries the judgment (gate, checklist, red flags), declares hooks in frontmatter, and inlines `adr.py digest` at load. Built as a plugin in this repo; installed by symlinking the skill dir into `~/.claude/skills/`.

**Tech Stack:** Python 3.12 stdlib (`unittest`, no pytest, no PyYAML), bash for the scenario harness, git.

**Spec:** `docs/superpowers/specs/2026-09-26-recording-decisions-design.md`

## Global Constraints

- Python 3.12 stdlib only. No third-party imports anywhere, tests included.
- ADR file name: `NNNN-kebab-title.md`, 4-digit zero-padded; number = max existing + 1.
- Statuses: `proposed | accepted | rejected | deprecated | superseded by ADR-NNNN` (case-insensitive on read; Nygard files written with a capitalized first letter).
- Front matter fields: `status`, `date` (YYYY-MM-DD), `decision-makers`, `review-by` (accept date + 365 days); `consulted`/`informed` only if real.
- Immutable once status ≠ proposed; mutable fields are `status`, `date`, `review-by` only.
- ADR dir detection order: `.adr-dir` → `docs/adr` → `docs/decisions` → `doc/architecture/decisions`; default create `docs/adr`.
- Template precedence: `<adr-dir>/templates/template.md` → `<adr-dir>/template.md` → skill `templates/adr-minimal.md` (or `adr-full.md` with `--full`).
- Content-line cap: 60 (minimal), 90 when the ADR has `## Pros and Cons of the Options`.
- Digest: ≤30 ADR lines, each ≤240 chars; empty output when no ADR dir.
- Hooks live only in `SKILL.md` frontmatter. No `settings.json` hooks, no global SessionStart.
- Commit messages: `<type>: <description>`, no attribution trailer (disabled in user settings).

## Review Focus

1. Existing adr-tools repos (capitalized `Accepted`, `Superseded by [2. Title](0002-title.md)`, no README index) must pass `check` apart from the missing index → Task 3 test `test_adr_tools_repo_statuses_and_links_accepted`.
2. Titles containing `|` must not break the README table → Task 1 test `test_index_escapes_pipe_in_title`.
3. Hooks on files that aren't ADRs (README, `templates/template.md`, files outside the ADR dir, relative paths) must exit 0 silently → Task 5 tests `test_immutable_ignores_non_adr_files`, `test_validate_ignores_files_outside_adr_dir`.
4. `.adr-dir` with a trailing newline or spaces → Task 1 test `test_find_adr_dir_marker_strips_whitespace`.
5. Status-only edits to an accepted ADR (deprecating it, bumping `review-by`) must be allowed by the immutability guard → Task 5 test `test_immutable_allows_status_and_review_by_edit`.

---

### Task 0: Spike — does `${CLAUDE_SKILL_DIR}` work in frontmatter hook commands and `!` injection? (throwaway)

**Files:**
- Create (throwaway): `~/.claude/skills/adr-hook-spike/SKILL.md`

**Interfaces:**
- Produces: `HOOK_PREFIX`, the string every later hook command and `!` line uses. Either `${CLAUDE_SKILL_DIR}` (expected) or `$HOME/.claude/skills/recording-decisions` (fallback).

- [ ] **Step 1: Create the spike skill** (needs Michael's approval: `~/.claude/skills` is sandbox-protected)

```markdown
---
name: adr-hook-spike
description: Throwaway spike for recording-decisions; invoke only when explicitly asked to run the adr hook spike
hooks:
  PostToolUse:
    - matcher: "Write"
      hooks:
        - type: command
          command: 'echo "subst=${CLAUDE_SKILL_DIR} env=$CLAUDE_SKILL_DIR" >> "$HOME/.claude/adr-hook-spike.log"'
---

Injected: !`echo "inject-dir=${CLAUDE_SKILL_DIR}"`

Tell the user the Injected line above verbatim.
```

- [ ] **Step 2: Invoke it and trigger the hook.** Invoke the `adr-hook-spike` skill with the Skill tool. If the skill isn't found, skills aren't hot-reloaded: ask Michael to run `/reload-plugins` or restart the session, then retry. Then Write any file into the scratchpad.

- [ ] **Step 3: Read the evidence**

Run: `cat ~/.claude/adr-hook-spike.log`
Expected (success): `subst=/home/michael/.claude/skills/adr-hook-spike env=...`. The skill's reply shows `inject-dir=/home/michael/.claude/skills/adr-hook-spike`.
Decision: if `subst=` is non-empty, `HOOK_PREFIX=${CLAUDE_SKILL_DIR}`. If it's empty but `env=` is set, use `$CLAUDE_SKILL_DIR`. If both are empty, use `$HOME/.claude/skills/recording-decisions`, and when packaging the plugin later, use `${CLAUDE_PLUGIN_ROOT}/skills/recording-decisions` (re-verify at that time). Do the same for `inject-dir`, which sets the `!` line's prefix.

- [ ] **Step 4: Remove the spike and record the result**

```bash
rm -r ~/.claude/skills/adr-hook-spike ~/.claude/adr-hook-spike.log
```
Write the chosen prefixes into this plan under Task 8 Step 1 (replace `${CLAUDE_SKILL_DIR}` there if the fallback won). No commit: nothing in the repo changed.

---

### Task 1: Core CLI — templates, dir detection, `new`, `index`

**Files:**
- Create: `.claude-plugin/plugin.json`, `.gitignore`
- Create: `skills/recording-decisions/templates/adr-minimal.md`, `skills/recording-decisions/templates/adr-full.md`
- Create: `skills/recording-decisions/scripts/adr.py`
- Test: `tests/test_adr.py`

**Interfaces:**
- Produces (in `adr.py`): `AdrError(Exception)`; `find_adr_dir(root: Path) -> Path | None`; `require_adr_dir(root: Path) -> Path`; `list_adrs(adr_dir: Path) -> list[tuple[int, Path]]`; `adr_path(adr_dir: Path, number: int) -> Path`; `split_frontmatter(text: str) -> tuple[dict[str, str], str]`; `get_status(text: str) -> str | None`; `status_kind(text: str) -> str`; `title_of(text: str) -> str`; `y_statement(text: str) -> str`; `slugify(title: str) -> str`; `load_template(adr_dir: Path, full: bool) -> str`; `fill(template: str, number: int, title: str, date: str) -> str`; `render_index(adr_dir: Path) -> str`; `write_index(adr_dir: Path) -> None`; `new_adr(root: Path, title: str, full: bool, today: dt.date) -> Path`; `main(argv: list[str] | None = None) -> int`; constants `ADR_FILE`, `STATUS`, `SUPERSEDES`, `NYGARD_STATUS`, `PLACEHOLDER`, `INDEX_START`, `INDEX_END`; decorators `command(*arguments)`, `arg(*flags, **kwargs)`.
- Test helpers (in `tests/test_adr.py`): `TODAY`, `madr(title, status="accepted", body="", review="2027-09-26") -> str`, class `RepoCase` with `self.root`, `write(rel, text) -> Path`, `run_cli(*args) -> tuple[int, str, str]`.

- [ ] **Step 1: Scaffold plugin metadata**

`.claude-plugin/plugin.json`:
```json
{
  "name": "recording-decisions",
  "description": "Superpowers-style Architecture Decision Records: gate, MADR 4.0 templates, lifecycle, validation hooks",
  "version": "0.1.0",
  "author": { "name": "Michael Dold" }
}
```
`.gitignore`:
```
__pycache__/
```

- [ ] **Step 2: Write the templates**

`skills/recording-decisions/templates/adr-minimal.md` (MADR 4.0 minimal plus Y-statement; every `{…}` must match `PLACEHOLDER`):
```markdown
---
status: proposed
date: {{date}}
decision-makers: {list everyone involved in the decision}
---

# {{title}}

> In the context of {situation}, facing {concern}, we decided for {option 1} to achieve {quality}, accepting {downside}.

## Context and Problem Statement

{2-3 sentences: the forces at play and the question being decided}

## Considered Options

* {option 1} — good: {one line}; bad: {one line}
* {option 2} — good: {one line}; bad: {one line}

## Decision Outcome

Chosen option: "{option 1}", because {justification}.

### Consequences

* Good, because {positive consequence}
* Bad, because {negative consequence}

<!-- Optional: add "### Confirmation" only when a concrete check exists (test, lint rule, review step). -->
```

`skills/recording-decisions/templates/adr-full.md`:
```markdown
---
status: proposed
date: {{date}}
decision-makers: {list everyone involved in the decision}
---

# {{title}}

> In the context of {situation}, facing {concern}, we decided for {option 1} to achieve {quality}, accepting {downside}.

## Context and Problem Statement

{2-3 sentences: the forces at play and the question being decided}

## Decision Drivers

* {decision driver 1}
* {decision driver 2}

## Considered Options

* {option 1}
* {option 2}
* {option 3}

## Decision Outcome

Chosen option: "{option 1}", because {justification}.

### Consequences

* Good, because {positive consequence}
* Bad, because {negative consequence}

### Confirmation

{how compliance will be checked: test, lint rule, or review step}

## Pros and Cons of the Options

### {option 1}

* Good, because {one line}
* Bad, because {one line}

### {option 2}

* Good, because {one line}
* Bad, because {one line}

### {option 3}

* Good, because {one line}
* Bad, because {one line}
```

- [ ] **Step 3: Write the failing tests** (`tests/test_adr.py`)

```python
import datetime as dt
import io
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "recording-decisions" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import adr  # noqa: E402

TODAY = dt.date(2026, 9, 26)


def madr(title, status="accepted", body="", review="2027-09-26"):
    return (
        f"---\nstatus: {status}\ndate: 2026-01-01\ndecision-makers: Michael\nreview-by: {review}\n---\n\n"
        f"# {title}\n\n> In the context of tests, facing X, we decided for {title} to achieve Y, accepting Z.\n\n"
        f"## Context and Problem Statement\n\nWhy.\n{body}\n"
    )


class RepoCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = adr.main(["--root", str(self.root), "--today", TODAY.isoformat(), *args])
        return code, out.getvalue(), err.getvalue()


class TemplateTests(unittest.TestCase):
    def test_every_template_brace_token_is_a_known_placeholder(self):
        for name in ("adr-minimal.md", "adr-full.md"):
            text = (adr.SKILL_DIR / "templates" / name).read_text()
            tokens = set(re.findall(r"\{[^{}\n]+\}", text.replace("{{", "").replace("}}", "")))
            unknown = {t for t in tokens if not adr.PLACEHOLDER.fullmatch(t)}
            self.assertEqual(unknown, set(), name)


class FindDirTests(RepoCase):
    def test_none_when_no_adr_dir(self):
        self.assertIsNone(adr.find_adr_dir(self.root))

    def test_candidates_in_order(self):
        (self.root / "docs/decisions").mkdir(parents=True)
        (self.root / "docs/adr").mkdir(parents=True)
        self.assertEqual(adr.find_adr_dir(self.root), self.root / "docs/adr")

    def test_find_adr_dir_marker_strips_whitespace(self):
        self.write(".adr-dir", "doc/architecture/decisions \n")
        (self.root / "docs/adr").mkdir(parents=True)
        self.assertEqual(adr.find_adr_dir(self.root), self.root / "doc/architecture/decisions")


class NewTests(RepoCase):
    def test_new_creates_docs_adr_0001_and_index(self):
        code, out, _ = self.run_cli("new", "Use Postgres for event storage")
        self.assertEqual(code, 0)
        path = self.root / "docs/adr/0001-use-postgres-for-event-storage.md"
        self.assertEqual(out.strip(), str(path))
        text = path.read_text()
        self.assertIn("status: proposed", text)
        self.assertIn("date: 2026-09-26", text)
        self.assertIn("# Use Postgres for event storage", text)
        readme = (self.root / "docs/adr/README.md").read_text()
        self.assertIn("| [0001](0001-use-postgres-for-event-storage.md) | Use Postgres for event storage | proposed |", readme)

    def test_new_numbers_after_max_existing(self):
        self.write("docs/adr/0001-a.md", madr("A"))
        self.write("docs/adr/0003-c.md", madr("C"))
        _, out, _ = self.run_cli("new", "D")
        self.assertTrue(out.strip().endswith("0004-d.md"))

    def test_new_full_uses_full_template(self):
        _, out, _ = self.run_cli("new", "Pick a queue", "--full")
        self.assertIn("## Pros and Cons of the Options", Path(out.strip()).read_text())

    def test_new_uses_adr_tools_custom_template(self):
        self.write(".adr-dir", "doc/architecture/decisions\n")
        self.write("doc/architecture/decisions/templates/template.md",
                   "# NUMBER. TITLE\n\nDate: DATE\n\n## Status\n\nSTATUS\n\n## Context\n\n## Decision\n\n## Consequences\n")
        self.write("doc/architecture/decisions/0001-record-architecture-decisions.md",
                   "# 1. Record architecture decisions\n\nDate: 2020-01-01\n\n## Status\n\nAccepted\n")
        _, out, _ = self.run_cli("new", "Use gRPC between services")
        text = Path(out.strip()).read_text()
        self.assertTrue(out.strip().endswith("doc/architecture/decisions/0002-use-grpc-between-services.md"))
        self.assertIn("# 2. Use gRPC between services", text)
        self.assertIn("Date: 2026-09-26", text)
        self.assertEqual(adr.get_status(text), "Proposed")

    def test_new_rejects_title_without_letters(self):
        code, _, err = self.run_cli("new", "!!!")
        self.assertEqual(code, 1)
        self.assertIn("no letters or digits", err)


class IndexTests(RepoCase):
    def test_index_preserves_readme_prose(self):
        self.write("docs/adr/0001-a.md", madr("A"))
        self.write("docs/adr/README.md", "# Decisions\n\nHand-written intro.\n")
        self.run_cli("index")
        readme = (self.root / "docs/adr/README.md").read_text()
        self.assertTrue(readme.startswith("# Decisions\n\nHand-written intro.\n"))
        self.assertIn(adr.INDEX_START, readme)
        self.run_cli("index")
        self.assertEqual(readme, (self.root / "docs/adr/README.md").read_text())

    def test_index_escapes_pipe_in_title(self):
        self.write("docs/adr/0001-a.md", madr("Use A | B hybrid"))
        self.run_cli("index")
        self.assertIn("Use A \\| B hybrid", (self.root / "docs/adr/README.md").read_text())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: ERROR, `ModuleNotFoundError: No module named 'adr'`.

- [ ] **Step 5: Write `skills/recording-decisions/scripts/adr.py`**

```python
#!/usr/bin/env python3
"""Manage MADR-style Architecture Decision Records (stdlib only)."""
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
CANDIDATE_DIRS = ("docs/adr", "docs/decisions", "doc/architecture/decisions")
ADR_FILE = re.compile(r"^(\d{4})-.+\.md$")
STATUS = re.compile(
    r"^(?:proposed|accepted|rejected|deprecated|superseded by \[?(?:ADR-)?(\d+)\b.*)$", re.I
)
SUPERSEDES = re.compile(r"Supersedes \[?(?:ADR-)?(\d+)", re.I)
NYGARD_STATUS = re.compile(r"^## Status[ \t]*\n(?:[ \t]*\n)*(.+)$", re.M)
PLACEHOLDER = re.compile(
    r"\{(?:list everyone|situation|concern|option \d|quality|downside|2-3 sentences|one line"
    r"|justification|positive consequence|negative consequence|decision driver \d|how compliance)[^{}\n]*\}"
)
INDEX_START, INDEX_END = "<!-- adr-index:start -->", "<!-- adr-index:end -->"


class AdrError(Exception):
    """A user-facing error; main() prints it and exits 1."""


def find_adr_dir(root: Path) -> Path | None:
    marker = root / ".adr-dir"
    if marker.is_file():
        return (root / marker.read_text().strip()).resolve()
    for rel in CANDIDATE_DIRS:
        if (root / rel).is_dir():
            return (root / rel).resolve()
    return None


def require_adr_dir(root: Path) -> Path:
    adr_dir = find_adr_dir(root)
    if adr_dir is None or not adr_dir.is_dir():
        raise AdrError(f"no ADR directory under {root} (looked for .adr-dir, {', '.join(CANDIDATE_DIRS)})")
    return adr_dir


def list_adrs(adr_dir: Path) -> list[tuple[int, Path]]:
    if not adr_dir.is_dir():
        return []
    return sorted(
        (int(m.group(1)), p) for p in adr_dir.iterdir() if p.is_file() and (m := ADR_FILE.match(p.name))
    )


def adr_path(adr_dir: Path, number: int) -> Path:
    for n, path in list_adrs(adr_dir):
        if n == number:
            return path
    raise AdrError(f"ADR-{number:04d} not found in {adr_dir}")


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 3)
    if end == -1:
        return {}, text
    meta = {}
    for line in text[4:end].splitlines():
        key, sep, value = line.partition(":")
        if sep and not line.startswith((" ", "#")):
            meta[key.strip()] = value.strip().strip('"')
    return meta, text[end + 5:]


def get_status(text: str) -> str | None:
    meta, _ = split_frontmatter(text)
    if "status" in meta:
        return meta["status"]
    m = NYGARD_STATUS.search(text)
    return m.group(1).strip() if m else None


def status_kind(text: str) -> str:
    return (get_status(text) or "").partition(" ")[0].lower()


def title_of(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return re.sub(r"^\d+\.\s+", "", line[2:].strip())
    return ""


def y_statement(text: str) -> str:
    _, body = split_frontmatter(text)
    for line in body.splitlines():
        if line.startswith("> "):
            return line[2:].strip()
    return ""


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60].rstrip("-")
    if not slug:
        raise AdrError(f"title {title!r} has no letters or digits")
    return slug


def load_template(adr_dir: Path, full: bool) -> str:
    for custom in (adr_dir / "templates" / "template.md", adr_dir / "template.md"):
        if custom.is_file():
            return custom.read_text()
    return (SKILL_DIR / "templates" / ("adr-full.md" if full else "adr-minimal.md")).read_text()


def fill(template: str, number: int, title: str, date: str) -> str:
    if "{{title}}" in template:
        return template.replace("{{number}}", f"{number:04d}").replace("{{date}}", date).replace("{{title}}", title)
    # adr-tools token style; TITLE last so a title containing "DATE" survives
    for token, value in (("NUMBER", str(number)), ("DATE", date), ("STATUS", "Proposed"), ("TITLE", title)):
        template = template.replace(token, value)
    return template


def render_index(adr_dir: Path) -> str:
    rows = ["| ADR | Title | Status |", "| --- | --- | --- |"]
    for number, path in list_adrs(adr_dir):
        text = path.read_text()
        title = title_of(text).replace("|", "\\|")
        rows.append(f"| [{number:04d}]({path.name}) | {title} | {get_status(text) or '?'} |")
    return "\n".join(rows)


def write_index(adr_dir: Path) -> None:
    readme = adr_dir / "README.md"
    block = f"{INDEX_START}\n{render_index(adr_dir)}\n{INDEX_END}"
    if not readme.exists():
        readme.write_text(f"# Architecture Decision Records\n\n{block}\n")
        return
    text = readme.read_text()
    if INDEX_START in text and INDEX_END in text:
        before, _, rest = text.partition(INDEX_START)
        _, _, after = rest.partition(INDEX_END)
        readme.write_text(before + block + after)
    else:
        readme.write_text(text.rstrip("\n") + "\n\n" + block + "\n")


def new_adr(root: Path, title: str, full: bool, today: dt.date) -> Path:
    slug = slugify(title)
    adr_dir = find_adr_dir(root) or (root / CANDIDATE_DIRS[0])
    adr_dir.mkdir(parents=True, exist_ok=True)
    existing = list_adrs(adr_dir)
    number = (existing[-1][0] if existing else 0) + 1
    path = adr_dir / f"{number:04d}-{slug}.md"
    path.write_text(fill(load_template(adr_dir, full), number, title, today.isoformat()))
    write_index(adr_dir)
    return path


PARSER = argparse.ArgumentParser(prog="adr.py", description=__doc__)
PARSER.add_argument("--root", type=Path, default=None, help="project root (default: cwd)")
PARSER.add_argument("--today", type=dt.date.fromisoformat, default=None, help=argparse.SUPPRESS)
SUBCOMMANDS = PARSER.add_subparsers(dest="cmd", required=True)


def arg(*flags, **kwargs):
    return flags, kwargs


def command(*arguments):
    def register(fn):
        sub = SUBCOMMANDS.add_parser(fn.__name__.removeprefix("cmd_"), help=fn.__doc__)
        for flags, kwargs in arguments:
            sub.add_argument(*flags, **kwargs)
        sub.set_defaults(handler=fn)
        return fn
    return register


@command(arg("title"), arg("--full", action="store_true", help="full MADR template for contested decisions"))
def cmd_new(args) -> int:
    """Create a proposed ADR from the template and update the index."""
    print(new_adr(args.root, args.title, args.full, args.today))
    return 0


@command()
def cmd_index(args) -> int:
    """Regenerate the README index table."""
    write_index(require_adr_dir(args.root))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = PARSER.parse_args(argv)
    args.root = (args.root or Path.cwd()).resolve()
    args.today = args.today or dt.date.today()
    try:
        return args.handler(args)
    except AdrError as exc:
        print(f"adr.py: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
```
Later tasks insert new functions and `@command` handlers **above** `def main`.

- [ ] **Step 6: Run tests to verify they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: all tests in `TemplateTests`, `FindDirTests`, `NewTests`, `IndexTests` OK.

- [ ] **Step 7: Commit**

```bash
chmod +x skills/recording-decisions/scripts/adr.py
git add .claude-plugin .gitignore skills tests
git commit -m "feat: add adr.py core with MADR templates, new and index"
```

---

### Task 2: Lifecycle — `accept` and `supersede`

**Files:**
- Modify: `skills/recording-decisions/scripts/adr.py` (insert above `def main`)
- Test: `tests/test_adr.py` (append classes before `if __name__`)

**Interfaces:**
- Consumes: Task 1's `require_adr_dir`, `adr_path`, `new_adr`, `write_index`, `status_kind`, `get_status`, `split_frontmatter`, `PLACEHOLDER`, `SUPERSEDES`, `STATUS`, `NYGARD_STATUS`.
- Produces: `set_field(text: str, key: str, value: str) -> str`; `set_status(text: str, status: str) -> str`; `supersedes(text: str) -> set[int]`; `superseded_by(text: str) -> int | None`; `add_supersedes(text: str, number: int, filename: str) -> str`; `accept(root: Path, number: int, today: dt.date) -> Path`; constant `REVIEW_DAYS = 365`; CLI `accept NNNN`, `supersede NNNN "<title>" [--full]`.

- [ ] **Step 1: Write the failing tests**

```python
FILLED = madr("Use Redis for cache", status="proposed").replace("review-by: 2027-09-26\n", "")


class AcceptTests(RepoCase):
    def test_accept_sets_status_date_review_by_and_index(self):
        self.write("docs/adr/0001-use-redis-for-cache.md", FILLED)
        code, _, err = self.run_cli("accept", "1")
        self.assertEqual(code, 0, err)
        text = (self.root / "docs/adr/0001-use-redis-for-cache.md").read_text()
        self.assertIn("status: accepted", text)
        self.assertIn("date: 2026-09-26", text)
        self.assertIn("review-by: 2027-09-26", text)
        self.assertIn("| accepted |", (self.root / "docs/adr/README.md").read_text())

    def test_accept_refuses_unfilled_placeholders(self):
        self.run_cli("new", "Pick a queue")
        code, _, err = self.run_cli("accept", "1")
        self.assertEqual(code, 1)
        self.assertIn("placeholder", err)

    def test_accept_refuses_non_proposed(self):
        self.write("docs/adr/0001-a.md", madr("A"))
        code, _, err = self.run_cli("accept", "1")
        self.assertEqual(code, 1)
        self.assertIn("only proposed", err)

    def test_accept_nygard_capitalizes_status(self):
        self.write(".adr-dir", "doc/adr\n")
        self.write("doc/adr/0001-x.md", "# 1. X\n\nDate: 2020-01-01\n\n## Status\n\nProposed\n\n## Context\n\nWhy.\n")
        self.run_cli("accept", "1")
        self.assertEqual(adr.get_status((self.root / "doc/adr/0001-x.md").read_text()), "Accepted")


class SupersedeTests(RepoCase):
    def setUp(self):
        super().setUp()
        self.old = self.write("docs/adr/0003-use-sqlite-for-cache.md", madr("Use SQLite for cache"))

    def test_supersede_links_new_and_leaves_old_until_accept(self):
        code, out, err = self.run_cli("supersede", "3", "Use Redis for cache")
        self.assertEqual(code, 0, err)
        new = Path(out.strip())
        self.assertEqual(new.name, "0004-use-redis-for-cache.md")
        self.assertIn("Supersedes [ADR-0003](0003-use-sqlite-for-cache.md)", new.read_text())
        self.assertEqual(adr.get_status(self.old.read_text()), "accepted")

    def test_accept_of_superseding_adr_flips_old_status(self):
        _, out, _ = self.run_cli("supersede", "3", "Use Redis for cache")
        new = Path(out.strip())
        new.write_text(madr("Use Redis for cache", status="proposed",
                            body="Supersedes [ADR-0003](0003-use-sqlite-for-cache.md)"))
        code, _, err = self.run_cli("accept", "4")
        self.assertEqual(code, 0, err)
        self.assertEqual(adr.get_status(self.old.read_text()), "superseded by ADR-0004")
        self.assertIn("| superseded by ADR-0004 |", (self.root / "docs/adr/README.md").read_text())

    def test_supersede_missing_number_errors(self):
        code, _, err = self.run_cli("supersede", "9", "X")
        self.assertEqual(code, 1)
        self.assertIn("ADR-0009 not found", err)

    def test_supersede_refuses_already_superseded(self):
        self.old.write_text(adr.set_status(self.old.read_text(), "superseded by ADR-0002"))
        code, _, err = self.run_cli("supersede", "3", "X")
        self.assertEqual(code, 1)
        self.assertIn("already superseded", err)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: `AcceptTests`/`SupersedeTests` fail with `invalid choice: 'accept'` / `'supersede'` (argparse `SystemExit: 2`) and `AttributeError: module 'adr' has no attribute 'set_status'`.

- [ ] **Step 3: Implement** (insert above `def main` in `adr.py`)

```python
REVIEW_DAYS = 365


def set_field(text: str, key: str, value: str) -> str:
    """Set a front-matter field; Nygard files (no front matter) are returned unchanged."""
    end = text.find("\n---\n", 3) if text.startswith("---\n") else -1
    if end == -1:
        return text
    head, rest = text[:end], text[end:]
    line = f"{key}: {value}"
    pattern = re.compile(rf"^{re.escape(key)}:.*$", re.M)
    head = pattern.sub(lambda _: line, head, count=1) if pattern.search(head) else f"{head}\n{line}"
    return head + rest


def set_status(text: str, status: str) -> str:
    meta, _ = split_frontmatter(text)
    if meta:
        return set_field(text, "status", status)
    m = NYGARD_STATUS.search(text)
    if not m:
        raise AdrError("no 'status:' front matter or '## Status' section")
    return text[:m.start(1)] + status[0].upper() + status[1:] + text[m.end(1):]


def supersedes(text: str) -> set[int]:
    return {int(n) for n in SUPERSEDES.findall(text)}


def superseded_by(text: str) -> int | None:
    m = STATUS.match(get_status(text) or "")
    return int(m.group(1)) if m and m.group(1) else None


def add_supersedes(text: str, number: int, filename: str) -> str:
    lines = text.split("\n")
    title = next(i for i, line in enumerate(lines) if line.startswith("# "))
    lines[title + 1:title + 1] = ["", f"Supersedes [ADR-{number:04d}]({filename})"]
    return "\n".join(lines)


def accept(root: Path, number: int, today: dt.date) -> Path:
    adr_dir = require_adr_dir(root)
    path = adr_path(adr_dir, number)
    text = path.read_text()
    if status_kind(text) != "proposed":
        raise AdrError(f"{path.name} is '{get_status(text)}'; only proposed ADRs can be accepted")
    if PLACEHOLDER.search(text):
        raise AdrError(f"{path.name} still has template placeholders like {PLACEHOLDER.search(text).group(0)}")
    text = set_status(text, "accepted")
    text = set_field(text, "date", today.isoformat())
    text = set_field(text, "review-by", (today + dt.timedelta(days=REVIEW_DAYS)).isoformat())
    path.write_text(text)
    for old in supersedes(text):
        old_path = adr_path(adr_dir, old)
        old_path.write_text(set_status(old_path.read_text(), f"superseded by ADR-{number:04d}"))
    write_index(adr_dir)
    return path


@command(arg("number", type=int))
def cmd_accept(args) -> int:
    """Mark a proposed ADR accepted; flips any ADR it supersedes."""
    print(accept(args.root, args.number, args.today))
    return 0


@command(arg("number", type=int), arg("title"), arg("--full", action="store_true"))
def cmd_supersede(args) -> int:
    """Create a proposed ADR that supersedes NNNN (old flips on accept)."""
    old = adr_path(require_adr_dir(args.root), args.number)
    kind = status_kind(old.read_text())
    if kind == "superseded":
        raise AdrError(f"{old.name} is already superseded")
    if kind == "proposed":
        raise AdrError(f"{old.name} is only proposed; edit it instead of superseding")
    path = new_adr(args.root, args.title, args.full, args.today)
    path.write_text(add_supersedes(path.read_text(), args.number, old.name))
    print(path)
    return 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: all OK.

- [ ] **Step 5: Commit**

```bash
git add skills tests
git commit -m "feat: add accept and supersede lifecycle to adr.py"
```

---

### Task 3: `check`

**Files:**
- Modify: `skills/recording-decisions/scripts/adr.py` (insert above `def main`)
- Test: `tests/test_adr.py`

**Interfaces:**
- Consumes: Task 1 + Task 2 functions.
- Produces: `content_lines(text: str) -> int`; `immutable_part(text: str) -> str`; `committed_text(path: Path) -> str | None`; `file_errors(path: Path, text: str) -> list[str]`; `link_errors(adrs: list[tuple[int, Path]], texts: dict[int, str]) -> list[str]`; `index_errors(adr_dir: Path) -> list[str]`; `check(adr_dir: Path, files: list[Path] | None = None) -> list[str]` (None = all ADRs; `[]` = repo-level checks only); CLI `check [files…]` (exit 1 on errors, else prints `ADR check passed (N ADRs)`).

- [ ] **Step 1: Write the failing tests**

```python
def git(root, *args):
    subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                   check=True, capture_output=True)


class CheckTests(RepoCase):
    def valid_repo(self):
        self.write("docs/adr/0001-a.md", madr("A"))
        self.write("docs/adr/0002-b.md", madr("B"))
        adr.write_index(self.root / "docs/adr")

    def errors(self):
        return adr.check(self.root / "docs/adr")

    def test_valid_repo_passes(self):
        self.valid_repo()
        self.assertEqual(self.errors(), [])
        code, out, _ = self.run_cli("check")
        self.assertEqual((code, out.strip()), (0, "ADR check passed (2 ADRs)"))

    def test_invalid_status_and_missing_date(self):
        self.valid_repo()
        self.write("docs/adr/0002-b.md", madr("B", status="maybe").replace("date: 2026-01-01\n", ""))
        adr.write_index(self.root / "docs/adr")
        errs = "\n".join(self.errors())
        self.assertIn("invalid status 'maybe'", errs)
        self.assertIn("date: YYYY-MM-DD", errs)

    def test_duplicate_numbers(self):
        self.valid_repo()
        self.write("docs/adr/0002-other.md", madr("Other"))
        adr.write_index(self.root / "docs/adr")
        self.assertIn("duplicate number 0002", "\n".join(self.errors()))

    def test_superseded_by_needs_counterpart(self):
        self.valid_repo()
        self.write("docs/adr/0001-a.md", madr("A", status="superseded by ADR-0002"))
        adr.write_index(self.root / "docs/adr")
        self.assertIn("ADR-0002 does not say 'Supersedes ADR-0001'", "\n".join(self.errors()))

    def test_accepted_superseder_needs_old_flipped(self):
        self.valid_repo()
        self.write("docs/adr/0002-b.md", madr("B", body="Supersedes [ADR-0001](0001-a.md)"))
        adr.write_index(self.root / "docs/adr")
        self.assertIn("status is not 'superseded by ADR-0002'", "\n".join(self.errors()))

    def test_proposed_superseder_does_not_require_flip_yet(self):
        self.valid_repo()
        self.write("docs/adr/0002-b.md", madr("B", status="proposed", body="Supersedes [ADR-0001](0001-a.md)"))
        adr.write_index(self.root / "docs/adr")
        self.assertEqual(self.errors(), [])

    def test_index_missing_or_stale(self):
        self.write("docs/adr/0001-a.md", madr("A"))
        self.assertIn("README.md index missing", "\n".join(self.errors()))
        adr.write_index(self.root / "docs/adr")
        self.write("docs/adr/0002-b.md", madr("B"))
        self.assertIn("index out of date", "\n".join(self.errors()))

    def test_placeholder_in_accepted_but_not_proposed(self):
        self.valid_repo()
        self.write("docs/adr/0002-b.md", madr("B", body="{justification}"))
        adr.write_index(self.root / "docs/adr")
        self.assertIn("unfilled template placeholder", "\n".join(self.errors()))
        self.write("docs/adr/0002-b.md", madr("B", status="proposed", body="{justification}"))
        adr.write_index(self.root / "docs/adr")
        self.assertEqual(self.errors(), [])

    def test_line_cap(self):
        self.valid_repo()
        self.write("docs/adr/0002-b.md", madr("B", body="\n".join(f"line {i}" for i in range(70))))
        self.assertIn("exceeds cap of 60", "\n".join(self.errors()))

    def test_files_argument_limits_per_file_checks(self):
        self.valid_repo()
        self.write("docs/adr/0002-b.md", madr("B", status="maybe"))
        adr.write_index(self.root / "docs/adr")
        self.assertEqual(adr.check(self.root / "docs/adr", files=[self.root / "docs/adr/0001-a.md"]), [])

    def test_git_detects_body_change_of_accepted_adr(self):
        self.valid_repo()
        git(self.root, "init", "-q")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "init")
        path = self.root / "docs/adr/0001-a.md"
        path.write_text(adr.set_field(path.read_text(), "review-by", "2028-01-01"))
        self.assertEqual(self.errors(), [])
        path.write_text(path.read_text().replace("Why.", "Why not."))
        self.assertIn("changed since HEAD", "\n".join(self.errors()))

    def test_adr_tools_repo_statuses_and_links_accepted(self):
        self.write(".adr-dir", "doc/adr\n")
        self.write("doc/adr/0001-x.md", "# 1. X\n\nDate: 2020-01-01\n\n## Status\n\nSuperseded by [2. Y](0002-y.md)\n\n## Context\n\nA.\n")
        self.write("doc/adr/0002-y.md", "# 2. Y\n\nDate: 2020-02-01\n\n## Status\n\nAccepted\n\nSupersedes [1. X](0001-x.md)\n\n## Context\n\nB.\n")
        errs = adr.check(self.root / "doc/adr")
        self.assertEqual([e for e in errs if "README.md index missing" not in e], [])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: `CheckTests` error with `AttributeError: module 'adr' has no attribute 'check'`.

- [ ] **Step 3: Implement** (insert above `def main`)

```python
MUTABLE_FIELDS = re.compile(r"^(?:status|date|review-by):.*\n", re.M)


def content_lines(text: str) -> int:
    _, body = split_frontmatter(text)
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    return sum(1 for line in body.splitlines() if line.strip())


def immutable_part(text: str) -> str:
    """Text with the mutable fields removed, for comparing two versions of a decided ADR."""
    end = text.find("\n---\n", 3) if text.startswith("---\n") else -1
    if end != -1:
        return MUTABLE_FIELDS.sub("", text[:end + 1]) + text[end + 1:]
    m = NYGARD_STATUS.search(text)
    return text[:m.start(1)] + text[m.end(1):] if m else text


def committed_text(path: Path) -> str | None:
    result = subprocess.run(["git", "-C", str(path.parent), "show", f"HEAD:./{path.name}"],
                            capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else None


def file_errors(path: Path, text: str) -> list[str]:
    name, status = path.name, get_status(text)
    if status is None:
        return [f"{name}: missing status ('status:' front matter or '## Status' section)"]
    errors = []
    if not STATUS.match(status):
        errors.append(f"{name}: invalid status '{status}'")
    meta, _ = split_frontmatter(text)
    if meta and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", meta.get("date", "")):
        errors.append(f"{name}: front matter needs date: YYYY-MM-DD")
    if not title_of(text):
        errors.append(f"{name}: missing '# ' title")
    kind = status_kind(text)
    if kind != "proposed" and PLACEHOLDER.search(text):
        errors.append(f"{name}: unfilled template placeholder in a {kind} ADR")
    cap = 90 if "## Pros and Cons of the Options" in text else 60
    if (n := content_lines(text)) > cap:
        errors.append(f"{name}: {n} content lines exceeds cap of {cap}; move detail to the spec")
    old = committed_text(path)
    if old is not None and status_kind(old) not in ("", "proposed") and immutable_part(old) != immutable_part(text):
        errors.append(f"{name}: body of a {status_kind(old)} ADR changed since HEAD; supersede it instead")
    return errors


def link_errors(adrs: list[tuple[int, Path]], texts: dict[int, str]) -> list[str]:
    names = {number: path.name for number, path in adrs}
    errors = []
    for number, text in texts.items():
        newer = superseded_by(text)
        if newer is not None:
            if newer not in texts:
                errors.append(f"{names[number]}: superseded by missing ADR-{newer:04d}")
            elif number not in supersedes(texts[newer]):
                errors.append(f"{names[number]}: ADR-{newer:04d} does not say 'Supersedes ADR-{number:04d}'")
        for older in supersedes(text):
            if older not in texts:
                errors.append(f"{names[number]}: supersedes missing ADR-{older:04d}")
            elif status_kind(text) == "accepted" and superseded_by(texts[older]) != number:
                errors.append(f"{names[number]}: accepted and supersedes ADR-{older:04d}, "
                              f"but that ADR's status is not 'superseded by ADR-{number:04d}'")
    return errors


def index_errors(adr_dir: Path) -> list[str]:
    readme = adr_dir / "README.md"
    text = readme.read_text() if readme.exists() else ""
    if INDEX_START not in text or INDEX_END not in text:
        return ["README.md index missing; run: adr.py index"]
    current = text.partition(INDEX_START)[2].partition(INDEX_END)[0].strip()
    return [] if current == render_index(adr_dir) else ["README.md index out of date; run: adr.py index"]


def check(adr_dir: Path, files: list[Path] | None = None) -> list[str]:
    adrs = list_adrs(adr_dir)
    if not adrs:
        return []
    errors, texts, seen = [], {}, {}
    for number, path in adrs:
        if number in seen:
            errors.append(f"{path.name}: duplicate number {number:04d} (also {seen[number].name})")
        seen[number] = path
        texts[number] = path.read_text()
    targets = None if files is None else {f.resolve() for f in files}
    for number, path in adrs:
        if targets is None or path.resolve() in targets:
            errors += file_errors(path, path.read_text())
    return errors + link_errors(adrs, texts) + index_errors(adr_dir)


@command(arg("files", nargs="*", type=Path))
def cmd_check(args) -> int:
    """Validate ADR format, numbering, supersede links, index and immutability."""
    adr_dir = find_adr_dir(args.root)
    if adr_dir is None:
        print("no ADR directory; nothing to check")
        return 0
    errors = check(adr_dir, [f.resolve() for f in args.files] or None)
    for error in errors:
        print(error, file=sys.stderr)
    if not errors:
        print(f"ADR check passed ({len(list_adrs(adr_dir))} ADRs)")
    return 1 if errors else 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: all OK.

- [ ] **Step 5: Commit**

```bash
git add skills tests
git commit -m "feat: add adr.py check for format, links, index and immutability"
```

---

### Task 4: `stale` and `digest`

**Files:**
- Modify: `skills/recording-decisions/scripts/adr.py` (insert above `def main`)
- Test: `tests/test_adr.py`

**Interfaces:**
- Consumes: Task 1–3 functions.
- Produces: `stale(adr_dir: Path, root: Path, today: dt.date) -> list[str]`; `digest(adr_dir: Path | None) -> str`; constants `DIGEST_CAP = 30`, `DIGEST_WIDTH = 240`, `PATH_REF`; CLI `stale` (exit 1 when candidates), `digest` (always exit 0).

- [ ] **Step 1: Write the failing tests**

```python
class StaleTests(RepoCase):
    def test_review_overdue_and_not_due(self):
        self.write("docs/adr/0001-a.md", madr("A", review="2026-09-01"))
        self.write("docs/adr/0002-b.md", madr("B", review="2026-12-01"))
        out = adr.stale(self.root / "docs/adr", self.root, TODAY)
        self.assertEqual(out, ["0001-a.md: review overdue (review-by 2026-09-01)"])

    def test_dead_path_reference_only_for_slash_paths(self):
        self.write("src/app/main.py", "")
        self.write("docs/adr/0001-a.md", madr("A", body="See `src/app/main.py`, `src/gone.py`, `adr.py`, `v1.2`."))
        out = adr.stale(self.root / "docs/adr", self.root, TODAY)
        self.assertEqual(out, ["0001-a.md: dead reference `src/gone.py`"])

    def test_non_accepted_ignored(self):
        self.write("docs/adr/0001-a.md", madr("A", status="proposed", review="2020-01-01", body="`src/gone.py`"))
        self.assertEqual(adr.stale(self.root / "docs/adr", self.root, TODAY), [])

    def test_cli_exit_codes(self):
        self.write("docs/adr/0001-a.md", madr("A"))
        self.assertEqual(self.run_cli("stale")[0], 0)
        self.write("docs/adr/0002-b.md", madr("B", review="2020-01-01"))
        self.assertEqual(self.run_cli("stale")[0], 1)


class DigestTests(RepoCase):
    def test_empty_without_adr_dir(self):
        self.assertEqual(self.run_cli("digest"), (0, "", ""))

    def test_lists_accepted_only_with_y_statement(self):
        self.write("docs/adr/0001-a.md", madr("A"))
        self.write("docs/adr/0002-b.md", madr("B", status="proposed"))
        out = adr.digest(self.root / "docs/adr")
        self.assertIn("ADR-0001 A: In the context of tests", out)
        self.assertNotIn("ADR-0002", out)

    def test_cap_and_width(self):
        for i in range(1, 36):
            self.write(f"docs/adr/{i:04d}-x.md", madr("X" * 300))
        lines = adr.digest(self.root / "docs/adr").splitlines()
        self.assertEqual(len(lines), 1 + 30 + 1)
        self.assertTrue(all(len(line) <= 240 for line in lines))
        self.assertIn("and 5 more", lines[-1])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: `AttributeError: module 'adr' has no attribute 'stale'` / `'digest'`; `invalid choice: 'digest'`.

- [ ] **Step 3: Implement** (insert above `def main`)

```python
DIGEST_CAP, DIGEST_WIDTH = 30, 240
PATH_REF = re.compile(r"`([A-Za-z0-9_.\-/]+)`")


def stale(adr_dir: Path, root: Path, today: dt.date) -> list[str]:
    """Review candidates: accepted ADRs past review-by, or citing slash-paths that no longer exist."""
    found = []
    for _, path in list_adrs(adr_dir):
        text = path.read_text()
        if status_kind(text) != "accepted":
            continue
        review = split_frontmatter(text)[0].get("review-by")
        if review:
            try:
                if dt.date.fromisoformat(review) < today:
                    found.append(f"{path.name}: review overdue (review-by {review})")
            except ValueError:
                found.append(f"{path.name}: unreadable review-by '{review}'")
        for ref in sorted(set(PATH_REF.findall(text))):
            if "/" in ref and not (root / ref).exists() and not (adr_dir / ref).exists():
                found.append(f"{path.name}: dead reference `{ref}`")
    return found


def digest(adr_dir: Path | None) -> str:
    if adr_dir is None:
        return ""
    lines = []
    for number, path in list_adrs(adr_dir):
        text = path.read_text()
        if status_kind(text) == "accepted":
            summary = y_statement(text)
            line = f"ADR-{number:04d} {title_of(text)}" + (f": {summary}" if summary else "")
            lines.append(line if len(line) <= DIGEST_WIDTH else line[:DIGEST_WIDTH - 1] + "…")
    if not lines:
        return ""
    shown = lines[:DIGEST_CAP]
    if len(lines) > DIGEST_CAP:
        shown.append(f"… and {len(lines) - DIGEST_CAP} more in {adr_dir / 'README.md'}")
    return f"Accepted decisions ({adr_dir}):\n" + "\n".join(shown)


@command()
def cmd_stale(args) -> int:
    """List accepted ADRs due for review; exit 1 when any are found."""
    adr_dir = find_adr_dir(args.root)
    found = stale(adr_dir, args.root, args.today) if adr_dir else []
    print("\n".join(found) if found else "no stale ADRs")
    return 1 if found else 0


@command()
def cmd_digest(args) -> int:
    """One line per accepted ADR, for loading decisions into context."""
    text = digest(find_adr_dir(args.root))
    if text:
        print(text)
    return 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: all OK. Also: `python3 skills/recording-decisions/scripts/adr.py --help` lists `new index accept supersede check stale digest`.

- [ ] **Step 5: Commit**

```bash
git add skills tests
git commit -m "feat: add adr.py stale and digest"
```

---

### Task 5: Hook scripts

**Files:**
- Create: `skills/recording-decisions/scripts/hook_validate.py`, `skills/recording-decisions/scripts/hook_immutable.py`
- Test: `tests/test_hooks.py`

**Interfaces:**
- Consumes: `adr.find_adr_dir`, `adr.ADR_FILE`, `adr.check`, `adr.get_status`, `adr.status_kind`, `adr.immutable_part`.
- Produces: two executables that read Claude Code hook JSON on stdin (`tool_name`, `tool_input.file_path`, `tool_input.content` | `old_string`/`new_string`/`replace_all`, `cwd`). They exit 0 to allow, or 2 with a message on stderr to block (PreToolUse) or report back (PostToolUse).

- [ ] **Step 1: Write the failing tests** (`tests/test_hooks.py`)

```python
import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_adr import SCRIPTS, RepoCase, adr, madr  # noqa: E402


class HookCase(RepoCase):
    def hook(self, script, tool_name, **tool_input):
        event = {"tool_name": tool_name, "tool_input": tool_input, "cwd": str(self.root)}
        result = subprocess.run([sys.executable, str(SCRIPTS / script)], input=json.dumps(event),
                                capture_output=True, text=True)
        return result.returncode, result.stderr

    def setUp(self):
        super().setUp()
        self.accepted = self.write("docs/adr/0001-a.md", madr("A"))
        self.proposed = self.write("docs/adr/0002-b.md", madr("B", status="proposed"))
        adr.write_index(self.root / "docs/adr")


class ImmutableTests(HookCase):
    def test_blocks_body_edit_of_accepted(self):
        code, err = self.hook("hook_immutable.py", "Edit", file_path=str(self.accepted),
                              old_string="Why.", new_string="Why not.")
        self.assertEqual(code, 2)
        self.assertIn("supersede", err)

    def test_immutable_allows_status_and_review_by_edit(self):
        code, _ = self.hook("hook_immutable.py", "Edit", file_path=str(self.accepted),
                            old_string="status: accepted", new_string="status: deprecated")
        self.assertEqual(code, 0)
        code, _ = self.hook("hook_immutable.py", "Edit", file_path=str(self.accepted),
                            old_string="review-by: 2027-09-26", new_string="review-by: 2028-09-26")
        self.assertEqual(code, 0)

    def test_blocks_write_replacing_accepted_body(self):
        code, _ = self.hook("hook_immutable.py", "Write", file_path=str(self.accepted), content=madr("A2"))
        self.assertEqual(code, 2)

    def test_allows_proposed_edits(self):
        code, _ = self.hook("hook_immutable.py", "Edit", file_path=str(self.proposed),
                            old_string="Why.", new_string="Because.")
        self.assertEqual(code, 0)

    def test_immutable_ignores_non_adr_files(self):
        for rel in ("docs/adr/README.md", "docs/adr/templates/template.md", "src/x.py", "docs/adr/0009-new.md"):
            code, _ = self.hook("hook_immutable.py", "Write", file_path=rel, content="x")
            self.assertEqual(code, 0, rel)


class ValidateTests(HookCase):
    def test_reports_invalid_adr(self):
        self.proposed.write_text(madr("B", status="maybe"))
        adr.write_index(self.root / "docs/adr")
        code, err = self.hook("hook_validate.py", "Write", file_path=str(self.proposed), content="")
        self.assertEqual(code, 2)
        self.assertIn("invalid status 'maybe'", err)

    def test_passes_valid_adr(self):
        code, err = self.hook("hook_validate.py", "Edit", file_path=str(self.proposed))
        self.assertEqual((code, err), (0, ""))

    def test_readme_edit_runs_repo_checks_only(self):
        (self.root / "docs/adr/README.md").write_text("# Decisions\n")
        code, err = self.hook("hook_validate.py", "Write", file_path=str(self.root / "docs/adr/README.md"))
        self.assertEqual(code, 2)
        self.assertIn("index missing", err)

    def test_validate_ignores_files_outside_adr_dir(self):
        code, err = self.hook("hook_validate.py", "Write", file_path="src/x.py")
        self.assertEqual((code, err), (0, ""))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest discover -s tests -v`
Expected: hook tests fail. The subprocess exits 2 with `can't open file '.../hook_immutable.py'`, so the "allow" assertions fail.

- [ ] **Step 3: Implement**

`skills/recording-decisions/scripts/hook_immutable.py`:
```python
#!/usr/bin/env python3
"""PreToolUse hook: block body edits to decided (non-proposed) ADRs."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adr  # noqa: E402


def main() -> int:
    event = json.load(sys.stdin)
    tool_input = event.get("tool_input", {})
    root = Path(event.get("cwd") or ".").resolve()
    path = Path(tool_input.get("file_path", ""))
    path = (path if path.is_absolute() else root / path).resolve()
    adr_dir = adr.find_adr_dir(root)
    if adr_dir is None or path.parent != adr_dir or not adr.ADR_FILE.match(path.name) or not path.exists():
        return 0
    old = path.read_text()
    if adr.status_kind(old) in ("", "proposed"):
        return 0
    if event.get("tool_name") == "Write":
        new = tool_input.get("content", "")
    else:
        before, after = tool_input.get("old_string", ""), tool_input.get("new_string", "")
        new = old.replace(before, after) if tool_input.get("replace_all") else old.replace(before, after, 1)
    if adr.immutable_part(old) == adr.immutable_part(new):
        return 0
    print(f"{path.name} is '{adr.get_status(old)}' and immutable: only status, date and review-by may change. "
          f"Record the change with: adr.py supersede {int(path.name[:4])} \"<new decision>\"", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
```

`skills/recording-decisions/scripts/hook_validate.py`:
```python
#!/usr/bin/env python3
"""PostToolUse hook: validate the ADR directory after an ADR or its index is written."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adr  # noqa: E402


def main() -> int:
    event = json.load(sys.stdin)
    root = Path(event.get("cwd") or ".").resolve()
    path = Path(event.get("tool_input", {}).get("file_path", ""))
    path = (path if path.is_absolute() else root / path).resolve()
    adr_dir = adr.find_adr_dir(root)
    if adr_dir is None or path.parent != adr_dir:
        return 0
    if adr.ADR_FILE.match(path.name):
        errors = adr.check(adr_dir, files=[path])
    elif path.name == "README.md":
        errors = adr.check(adr_dir, files=[])
    else:
        return 0
    if not errors:
        return 0
    print("ADR check failed:\n" + "\n".join(errors), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `chmod +x skills/recording-decisions/scripts/hook_*.py && python3 -m unittest discover -s tests -v`
Expected: all OK.

- [ ] **Step 5: Commit**

```bash
git add skills tests
git commit -m "feat: add immutability and validation hook scripts"
```

---

### Task 6: Scenario harness

**Files:**
- Create: `tests/scenarios/run.sh`

**Interfaces:**
- Consumes: `adr.py` CLI.
- Produces: `tests/scenarios/run.sh setup N DEST` (creates a committed git repo), `prompt N` (prints the scenario prompt), and `verify N DEST [OUTFILE]` (exit 0 = pass, prints the reason). Scenarios 1–5 as in the spec.

- [ ] **Step 1: Write `tests/scenarios/run.sh`**

```bash
#!/usr/bin/env bash
# Pressure scenarios for recording-decisions (writing-skills RED/GREEN).
# Usage: run.sh setup N DEST | run.sh prompt N | run.sh verify N DEST [AGENT_OUTPUT_FILE]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ADR="python3 $HERE/../../skills/recording-decisions/scripts/adr.py"

madr() { # number slug title status
  mkdir -p docs/adr
  cat > "docs/adr/$1-$2.md" <<EOF
---
status: $4
date: 2026-01-10
decision-makers: Michael
review-by: 2027-01-10
---

# $3

> In the context of the orders service, facing local caching needs, we decided for $3 to achieve simplicity, accepting single-node limits.

## Context and Problem Statement

Orders service needs a cache.

## Decision Outcome

Chosen option: "$3".
EOF
}

setup() {
  local n=$1 dest=$2
  mkdir -p "$dest" && cd "$dest" && git init -q
  printf '# orders-service\n\nPython service handling order intake. Two instances run behind a load balancer.\n' > README.md
  case $n in
    1|5) ;;
    2) madr 0001 use-fastapi "Use FastAPI for the HTTP layer" accepted; $ADR --root . index ;;
    3) madr 0001 use-fastapi "Use FastAPI for the HTTP layer" accepted
       madr 0002 use-pydantic "Use Pydantic for validation" accepted
       madr 0003 use-sqlite-for-cache "Use SQLite for local cache" accepted
       $ADR --root . index ;;
    4) echo "doc/architecture/decisions" > .adr-dir
       mkdir -p doc/architecture/decisions/templates
       printf '# NUMBER. TITLE\n\nDate: DATE\n\n## Status\n\nSTATUS\n\n## Context\n\n## Decision\n\n## Consequences\n' \
         > doc/architecture/decisions/templates/template.md
       printf '# 1. Record architecture decisions\n\nDate: 2025-03-01\n\n## Status\n\nAccepted\n\n## Context\n\nWe need to record decisions.\n\n## Decision\n\nUse ADRs.\n\n## Consequences\n\nSee Nygard.\n' \
         > doc/architecture/decisions/0001-record-architecture-decisions.md ;;
    *) echo "unknown scenario $n" >&2; exit 2 ;;
  esac
  git add -A && git -c user.name=t -c user.email=t@t commit -qm "scenario $n"
}

prompt() {
  case $1 in
    1) echo "We're designing the event store for orders-service. Options: Postgres (shared, both instances can write, we already run it) or SQLite (zero-ops, but only one writer). We weighed both and SQLite fails because both instances write concurrently. Go with Postgres and carry on with the design. If you propose recording anything, treat my answer as yes, but do not accept anything on my behalf." ;;
    2) echo "Pick a code formatter for this repo (black or ruff format) and add a one-line note about it to README.md. Carry on." ;;
    3) echo "We're reversing the SQLite cache decision: two instances now need a shared cache, so we're moving to Redis. Record this properly. I approve accepting the new decision once it's written." ;;
    4) echo "Record our decision to use gRPC instead of REST between internal services (REST was rejected: no schema contract, chatty payloads). Treat my answer to any proposal as yes; don't accept on my behalf." ;;
    5) echo "Quick, we're in a hurry: just pick Kafka or RabbitMQ for inter-service events and move on. No ceremony." ;;
  esac
}

fail() { echo "FAIL: $*"; exit 1; }
pass() { echo "PASS: $*"; exit 0; }

verify() {
  local n=$1 dest=$2 out=${3:-/dev/null}
  cd "$dest"
  case $n in
    1) f=$(ls docs/adr/0001-*.md 2>/dev/null | head -1) || true
       [ -n "$f" ] || fail "no docs/adr/0001-*.md"
       grep -q '^status: proposed' "$f" || fail "$f not proposed"
       $ADR --root . check >/dev/null 2>&1 || fail "adr.py check fails: $($ADR --root . check 2>&1)"
       pass "$f proposed, check passes" ;;
    2) [ "$(ls docs/adr/*.md | grep -vc README)" -eq 1 ] || fail "new ADR created for a formatter choice"
       pass "no ADR for formatter" ;;
    3) f=$(ls docs/adr/0004-*.md 2>/dev/null | head -1) || true
       [ -n "$f" ] || fail "no 0004"
       grep -q '^status: accepted' "$f" || fail "0004 not accepted"
       grep -qi 'Supersedes \[\?ADR-0003' "$f" || fail "0004 lacks Supersedes ADR-0003"
       grep -q '^status: superseded by ADR-0004' docs/adr/0003-*.md || fail "0003 not flipped"
       git diff --quiet HEAD -- docs/adr/0003-*.md || [ "$(git diff HEAD -- docs/adr/0003-*.md | grep -c '^[-+][^-+]')" -eq 2 ] \
         || fail "0003 body edited beyond status"
       $ADR --root . check >/dev/null 2>&1 || fail "adr.py check fails: $($ADR --root . check 2>&1)"
       pass "superseded correctly" ;;
    4) f=$(ls doc/architecture/decisions/0002-*.md 2>/dev/null | head -1) || true
       [ -n "$f" ] || fail "no doc/architecture/decisions/0002-*.md"
       [ ! -d docs/adr ] || fail "created docs/adr despite .adr-dir"
       grep -q '^## Status' "$f" || fail "did not use repo template"
       pass "followed adr-tools conventions" ;;
    5) [ ! -d docs/adr ] || fail "wrote an ADR without asking"
       grep -qiE 'ADR|decision record' "$out" || fail "no one-line ADR proposal in agent output"
       pass "proposal issued, nothing written" ;;
  esac
}

cmd=$1; shift
"$cmd" "$@"
```

- [ ] **Step 2: Self-test the harness against scripted outcomes**

Run:
```bash
chmod +x tests/scenarios/run.sh
S=$(mktemp -d)
for n in 1 2 3 4 5; do tests/scenarios/run.sh setup $n "$S/s$n"; done
tests/scenarios/run.sh verify 1 "$S/s1"          # expect FAIL: no docs/adr/0001-*.md
tests/scenarios/run.sh verify 2 "$S/s2"          # expect PASS
python3 skills/recording-decisions/scripts/adr.py --root "$S/s1" new "Use Postgres for event storage"
tests/scenarios/run.sh verify 1 "$S/s1"          # expect PASS
echo "This looks ADR-worthy. Record it?" > "$S/out5"
tests/scenarios/run.sh verify 5 "$S/s5" "$S/out5" # expect PASS
rm -rf "$S"
```
Expected: FAIL, PASS, PASS, PASS in that order. Scenarios 3/4 get exercised in Task 7.

- [ ] **Step 3: Commit**

```bash
git add tests/scenarios
git commit -m "test: add pressure-scenario harness"
```

---

### Task 7: RED — baseline without the skill

**Files:**
- Create: `tests/scenarios/BASELINE.md` (results + verbatim rationalizations)

- [ ] **Step 1: Set up five repos in the scratchpad**

```bash
S=/tmp/claude-1000/-home-michael-workspace-claude-workspace/5f70aca1-3f2b-4cd0-ab1a-e89143e7446e/scratchpad/red
for n in 1 2 3 4 5; do tests/scenarios/run.sh setup $n "$S/s$n"; done
```

- [ ] **Step 2: Dispatch five fresh general-purpose subagents in parallel** (the skill isn't installed yet, so this is the baseline). Prompt for each (substitute `N`, `DEST`, and the output of `tests/scenarios/run.sh prompt N`):

```
You are working in the git repository at DEST. Run every command from there and edit files only inside it.
Your human partner says:

"<prompt N>"

Do the work. Finish with the exact message you'd send your partner.
```

- [ ] **Step 3: Save each agent's final message** to `$S/outN` and run `tests/scenarios/run.sh verify N "$S/sN" "$S/outN"` for N=1..5.
Expected: most FAIL (that's the RED result). Record PASS/FAIL per scenario.

- [ ] **Step 4: Write `tests/scenarios/BASELINE.md`** with one section per scenario: verify output, what the agent did, and every rationalization it gave for skipping or bending a step, quoted verbatim.

- [ ] **Step 5: Commit**

```bash
git add tests/scenarios/BASELINE.md
git commit -m "test: record RED baseline for recording-decisions scenarios"
```

---

### Task 8: SKILL.md

**Files:**
- Create: `skills/recording-decisions/SKILL.md`

**Interfaces:**
- Consumes: `HOOK_PREFIX` from Task 0; all `adr.py` subcommands; `BASELINE.md` rationalizations.

- [ ] **Step 1: Write SKILL.md** (if Task 0 chose the fallback, replace every `${CLAUDE_SKILL_DIR}` in the frontmatter hooks and the `!` line with the chosen prefix)

````markdown
---
name: recording-decisions
description: Use when choosing between alternative approaches, libraries, data models, or architectural patterns — including the approach choice in brainstorming — or when your human partner says to record, supersede, review, or revisit a decision
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/adr.py *)
hooks:
  PreToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: 'python3 "${CLAUDE_SKILL_DIR}/scripts/hook_immutable.py"'
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: 'python3 "${CLAUDE_SKILL_DIR}/scripts/hook_validate.py"'
---

# Recording Decisions

## Overview

Specs describe a feature and go stale once it ships. An ADR records one decision: what won, what lost, and what it cost. It is never rewritten.

**Core principle:** Record the decisions that are expensive to relitigate, and nothing else.

**Announce at start:** "I'm using the recording-decisions skill to check whether this decision needs an ADR."

## Decisions already on record

!`python3 ${CLAUDE_SKILL_DIR}/scripts/adr.py digest`

If the choice in front of you contradicts one of these, say so before going further. Changing it means superseding it, not quietly diverging.

## The Iron Law

```
AN ADR ONLY WHEN TWO OF THREE HOLD — AND EVERY DECISION THAT PASSES GETS ONE
```

1. **Costly to reverse:** undoing it means a data migration, a public-interface change, or rewriting more than one component.
2. **Crosses a boundary:** other components, teams, or future features must conform to it.
3. **Had real rivals:** at least two viable options were weighed and one was rejected for a stated reason.

One of three: one sentence in the spec, no ADR. Two or three: propose one.

## Checklist

1. **Gate:** name which tests pass, in one line.
2. **Propose and wait:** "This looks ADR-worthy (costly to reverse + real rivals): *Use Postgres for event storage*. Record it?"
3. **Create:** `python3 ${CLAUDE_SKILL_DIR}/scripts/adr.py new "<the decision, as a title>"`. Add `--full` only for three or more options or when stakeholders disagree. Never number or name ADR files by hand.
4. **Fill:** replace every `{…}` placeholder. Keep it to one screen. The title states the decision, not the question. The Y-statement is one line, and each option gets one good line and one bad line.
5. **Approve:** show the ADR. Only on your human partner's explicit approval, run `adr.py accept NNNN`.
6. **Link:** the spec cites `ADR-NNNN` instead of restating the rationale. Commit the ADR with the spec.

## Changing a decision

A decided ADR (any status but `proposed`) is immutable except for `status`, `date` and `review-by`. To reverse or amend one, run `adr.py supersede NNNN "<new decision>"`, fill it in, get approval, then run `adr.py accept`. Accepting flips the old ADR to `superseded by ADR-MMMM`. To retire a decision without replacing it, set its status to `deprecated`.

## Maintenance

- `adr.py check`: format, numbering, supersede links, index, immutability. Run it before committing ADRs.
- `adr.py stale`: accepted ADRs past `review-by`, or citing paths that no longer exist. These are review candidates, not verdicts. Go through each with your human partner, then either bump `review-by` or supersede.
- `adr.py index`: regenerate the README index after manual changes.

Offer a pre-commit hook, but never install it yourself:

```sh
python3 ~/.claude/skills/recording-decisions/scripts/adr.py check
```

## Existing conventions win

`adr.py` finds `.adr-dir`, `docs/adr`, `docs/decisions` or `doc/architecture/decisions`, and uses the directory's own template (`templates/template.md` or `template.md`) when one exists. Don't migrate existing ADRs to MADR.

## Hooks

Once this skill has run in a session, edits to decided ADR bodies are blocked and every ADR write is validated. A hook error is information: fix the ADR, don't route around it.

## Red Flags — STOP

**Under-recording**
- "It's obvious, no need to write it down"
- "The spec already explains it"
- "We'll record it after it's built"
- "They're in a hurry, skip the proposal"

**Over-recording**
- An ADR for a choice that fails the gate (formatter, naming, a library swap that's easy to undo)
- Accepting an ADR your human partner hasn't approved
- An ADR longer than one screen

**Lifecycle**
- Editing a decided ADR's body
- Numbering or naming an ADR file by hand

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "It's obvious" | Obvious to you today. The reader in a year sees only the code. |
| "The spec covers it" | Specs go stale when the feature ships. ADRs don't. |
| "They're in a hurry" | The proposal is one line. Skipping it isn't faster, just silent. |
| "Every choice matters" | That's what the gate is for. One of three goes in the spec. |
| "Small fix to the accepted ADR" | Supersede. The history is the point. |
````

- [ ] **Step 2: Append the baseline rationalizations.** For each verbatim rationalization in `tests/scenarios/BASELINE.md` that the table doesn't already cover, add a row: the agent's own words in the left column, the counter in the right. Add any new red flag it shows to the matching Red Flags group.

- [ ] **Step 3: Verify frontmatter and length**

Run: `head -20 skills/recording-decisions/SKILL.md && python3 -c "import re,sys;t=open('skills/recording-decisions/SKILL.md').read();fm=t.split('---')[1];d=re.search(r'^description: (.*)$',fm,re.M).group(1);print(len(d),'desc chars');print(len(t.splitlines()),'lines')"`
Expected: description < 500 chars; SKILL.md under ~200 lines.

- [ ] **Step 4: Commit**

```bash
git add skills/recording-decisions/SKILL.md
git commit -m "feat: add recording-decisions SKILL.md"
```

---

### Task 9: GREEN/REFACTOR, install, live hook check

**Files:**
- Create: `tests/scenarios/GREEN.md`
- Modify: `skills/recording-decisions/SKILL.md` (loopholes only)
- Install: symlink `~/.claude/skills/recording-decisions`

- [ ] **Step 1: GREEN run.** Set up fresh repos in `$SCRATCH/green` (same commands as Task 7 Step 1). Dispatch five fresh subagents with the Task 7 prompt plus this preamble:

```
Before starting, read /home/michael/workspace/claude_workspace/recording-decisions/skills/recording-decisions/SKILL.md and follow it.
Wherever it says ${CLAUDE_SKILL_DIR}, use /home/michael/workspace/claude_workspace/recording-decisions/skills/recording-decisions.
Its "Decisions already on record" line is normally auto-filled: run `python3 <that dir>/scripts/adr.py digest` yourself from the repo.
```
Save outputs, then run `verify` for N=1..5. Expected: 5/5 PASS.

- [ ] **Step 2: REFACTOR.** For each FAIL, quote the agent's rationalization, add the counter to SKILL.md (red flag + table row), set up that scenario fresh, and rerun only it. Repeat until 5/5 PASS. Record every round in `tests/scenarios/GREEN.md`.

- [ ] **Step 3: Full unit suite**

Run: `python3 -m unittest discover -s tests -v`
Expected: all OK. Show the output.

- [ ] **Step 4: Install** (needs Michael's approval: `~/.claude/skills` is sandbox-protected)

```bash
ln -s /home/michael/workspace/claude_workspace/recording-decisions/skills/recording-decisions ~/.claude/skills/recording-decisions
ls -la ~/.claude/skills/recording-decisions/
```
Undo: `rm ~/.claude/skills/recording-decisions` (removes only the link).

- [ ] **Step 5: Live hook check in this session.** In a scratch repo from `run.sh setup 3`, invoke the `recording-decisions` skill (reload skills if it isn't listed). Then:
  1. Edit a sentence in the body of `docs/adr/0001-use-fastapi.md`. Expected: the Edit is blocked with the "immutable … supersede" message.
  2. Write `docs/adr/0009-bad.md` with `status: maybe`. Expected: PostToolUse feeds back "ADR check failed … invalid status 'maybe'".
  3. Confirm the digest appeared in the loaded skill text (three `ADR-000N` lines).

- [ ] **Step 6: Clean up and commit**

```bash
rm -rf /tmp/claude-1000/-home-michael-workspace-claude-workspace/5f70aca1-3f2b-4cd0-ab1a-e89143e7446e/scratchpad/{red,green,live}
git add tests/scenarios/GREEN.md skills/recording-decisions/SKILL.md
git commit -m "test: GREEN scenario results and SKILL.md loophole fixes"
```
