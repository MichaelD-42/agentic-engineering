# eliciting-needs Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A superpowers-style skill that takes a non-software engineer's first AI idea, extracts the real need onto a canvas, roasts it, classifies the solution mode (automate / augment / agent / classic / process change / don't build), sketches a solution from a stack profile, and hands off to superpowers:brainstorming.

**Architecture:** One stdlib-only CLI (`scripts/canvas.py`) owns canvas mechanics: scaffold, structural + completeness checks, status gates, HTML rendering. `SKILL.md` carries the judgment (iron law, checklist, red flags); three reference files (probes, AI fit, roast rubric) load on demand. The rendered HTML is one self-contained page used both as the superpowers visual-companion screen and as the take-away artifact. Built as a plugin in this repo, installed by symlink.

**Tech Stack:** Python 3.12 stdlib (runtime), pytest via uv (dev only), bash for the scenario harness, marked@18 + mermaid@12 from cdn.jsdelivr.net (client-side in the rendered page).

**Spec:** `docs/superpowers/specs/2026-09-26-eliciting-needs-design.md`

## Global Constraints

- Runtime is Python 3.12 stdlib only; pytest is a dev dependency only (`uv run pytest`).
- Canvas sections, exact H2 titles and order: `Original idea`, `Actual need`, `Actors`, `As-is process`, `Cost of the problem`, `Success criteria`, `Context diagram`, `Solution mode`, `Constraints and risks`, `Open questions`, `Roast`, `Solution sketch`.
- Scored (roasted) cells: `Actual need` … `Constraints and risks` (8 cells). Must score 2 to pass: `Actual need`, `Success criteria`, `Solution mode`.
- Frontmatter fields: `title`, `date` (YYYY-MM-DD), `status: draft|roasted|approved`, `owner`, `mode: automate|augment|agent|classic|process-change|dont-build` (empty until classified).
- Placeholder syntax: `{fill: …}`. Chosen over bare `{…}` because Mermaid uses `{…}` for decision nodes.
- Output location in the target project: `docs/needs/YYYY-MM-DD-<slug>/canvas.md` + `canvas.html`.
- Roast verdict line: `Verdict: pass|reroute|kill`. `kill` requires mode `process-change` or `dont-build`.
- CDN URLs, exact: `https://cdn.jsdelivr.net/npm/marked@18/lib/marked.umd.js`, `https://cdn.jsdelivr.net/npm/mermaid@12/dist/mermaid.min.js` (both verified 200 on 2026-09-26).
- Commit messages `<type>: <description>`, no attribution trailer (disabled in user settings).
- No installs into `~/.claude` without Michael's explicit approval.

## Review Focus

1. Titles with umlauts/punctuation ("Prüfung der Lieferanten-E-Mails!") must give a readable ASCII slug, not `pr-fung` → Task 1 test `test_slug_transliterates_umlauts`.
2. Canvases saved with Windows line endings (driver edits in Notepad) must parse → Task 2 test `test_crlf_canvas_parses`.
3. Mermaid decision nodes `B{Approved?}` must not be flagged as placeholders → Task 2 test `test_mermaid_braces_are_not_placeholders`.
4. Markdown containing `</script>` or `<!--` must not break or inject into the rendered page → Task 4 test `test_render_escapes_script_breakout`.
5. The word `status:` inside the canvas body must not be rewritten by a status transition → Task 3 test `test_status_only_touches_frontmatter`.

---

### Task 0: Prior-art search (research, no code)

**Files:** none (findings go into the Task 6 commit message body if they change anything).

- [ ] **Step 1:** Run `gh auth status`. If unauthenticated, ask Michael to run `! gh auth login`; if he declines, skip to Step 3 and note "prior-art search skipped: gh unauthenticated".
- [ ] **Step 2:** Run
```bash
gh search repos "requirements elicitation" --limit 20
gh search code "requirements elicitation" --filename SKILL.md --limit 20
gh search code "jobs to be done" --filename SKILL.md --limit 20
gh search code "AI use case canvas" --limit 20
```
Read any skill that elicits needs or classifies AI fit. Port proven probes or rubric criteria into Task 6 references; do not change the canvas structure (it is fixed by the spec).
- [ ] **Step 3:** Write two lines of findings in the session for Michael: what was found, what (if anything) will be ported.

---

### Task 1: Scaffold plugin, canvas template, `canvas.py new`

**Files:**
- Create: `.claude-plugin/plugin.json`, `pyproject.toml`, `.gitignore`
- Create: `skills/eliciting-needs/templates/need-canvas.md`
- Create: `skills/eliciting-needs/scripts/canvas.py`
- Test: `tests/test_canvas.py`

**Interfaces:**
- Produces (in `canvas.py`): constants `SECTIONS`, `SCORED`, `MUST_SCORE_2`, `STATUSES`, `MODES`, `NO_BUILD`, `FIELDS`, `PLACEHOLDER`, `FRONT`; `class CanvasError(Exception)`; `slugify(title: str) -> str`; `read(path: Path) -> str`; `parse(text: str) -> tuple[dict[str, str], dict[str, str]]`; `new(root: Path, title: str, today: dt.date, owner: str = "") -> Path`; `main(argv: list[str] | None = None) -> int`.

- [ ] **Step 1: Scaffold files**

`.claude-plugin/plugin.json`:
```json
{
  "name": "agentic-engineering",
  "description": "Agentic engineering skills: eliciting the real need behind AI use cases",
  "version": "0.1.0",
  "author": { "name": "Michael Dold" }
}
```

`pyproject.toml`:
```toml
[project]
name = "agentic-engineering"
version = "0.1.0"
description = "Agentic engineering skills plugin (runtime is stdlib-only)"
requires-python = ">=3.12"
dependencies = []

[dependency-groups]
dev = ["pytest>=9"]

[tool.uv]
package = false

[tool.pytest.ini_options]
testpaths = ["tests"]
```

`.gitignore`:
```
__pycache__/
.venv/
.pytest_cache/
.superpowers/
```

Run: `uv sync` — Expected: creates `.venv`, installs pytest.

- [ ] **Step 2: Write the canvas template** `skills/eliciting-needs/templates/need-canvas.md`:

````markdown
---
title: {{title}}
date: {{date}}
status: draft
owner: {{owner}}
mode:
---

<!-- Tag every claim (said) = the driver said it, or (assumed) = Claude inferred it. Replace each {fill: …}. -->

## Original idea

> {fill: the driver's first request, quoted verbatim}

## Actual need

{fill: [actor] needs to [job] so that [outcome]; today blocked by [obstacle]}

## Actors

- Has the problem: {fill: who}
- Pays for the solution: {fill: who}
- Operates it day to day: {fill: who}
- Affected by it: {fill: who}

## As-is process

```mermaid
flowchart LR
  A[{fill: trigger}] --> B[{fill: step}] --> C[{fill: result}]
```

Pain points: {fill: which steps hurt, and how}

## Cost of the problem

{fill: frequency × time / money / error rate, with confidence low|medium|high}

## Success criteria

| Metric | Baseline | Target |
|---|---|---|
| {fill: metric} | {fill: today, with unit} | {fill: goal, with unit} |

## Context diagram

```mermaid
flowchart LR
  U[{fill: actor}] --> S(({fill: the solution}))
  D[({fill: data source})] --> S
```

## Solution mode

Mode: {fill: automate | augment | agent | classic | process-change | dont-build}

{fill: deciding factors — structured input?, judgment needed?, error tolerance, output verifiable?, volume/frequency, data available?, cost per run}

## Constraints and risks

{fill: data protection/GDPR, compliance, budget, who owns it after launch}

## Open questions

- {fill: open question, or "none"}

## Roast

| Cell | Score | Why / fixing question |
|---|---|---|
| Actual need | {fill: 0-2} | {fill: why} |
| Actors | {fill: 0-2} | {fill: why} |
| As-is process | {fill: 0-2} | {fill: why} |
| Cost of the problem | {fill: 0-2} | {fill: why} |
| Success criteria | {fill: 0-2} | {fill: why} |
| Context diagram | {fill: 0-2} | {fill: why} |
| Solution mode | {fill: 0-2} | {fill: why} |
| Constraints and risks | {fill: 0-2} | {fill: why} |

Kill criteria: {fill: none fired, or which}

Verdict: {fill: pass | reroute | kill}

## Solution sketch

{fill: locked until the roast passes}
````

- [ ] **Step 3: Write the failing tests** `tests/test_canvas.py`:

```python
import datetime as dt
import io
import json
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "eliciting-needs" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import canvas  # noqa: E402

TODAY = dt.date(2026, 9, 26)


class RepoCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self):
        self._tmp.cleanup()

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = canvas.main(["--root", str(self.root), "--today", TODAY.isoformat(), *args])
        return code, out.getvalue(), err.getvalue()


class NewTest(RepoCase):
    def test_new_creates_dated_slug_dir_with_canvas(self):
        path = canvas.new(self.root, "Supplier email triage", TODAY, owner="Anna")
        self.assertEqual(path, self.root / "docs/needs/2026-09-26-supplier-email-triage/canvas.md")
        meta, sections = canvas.parse(path.read_text())
        self.assertEqual(meta["title"], "Supplier email triage")
        self.assertEqual(meta["date"], "2026-09-26")
        self.assertEqual(meta["status"], "draft")
        self.assertEqual(meta["owner"], "Anna")
        self.assertEqual(meta["mode"], "")
        self.assertEqual(list(sections), list(canvas.SECTIONS))

    def test_new_refuses_existing_dir(self):
        canvas.new(self.root, "Same", TODAY)
        with self.assertRaises(canvas.CanvasError):
            canvas.new(self.root, "Same", TODAY)

    def test_new_rejects_empty_title(self):
        with self.assertRaises(canvas.CanvasError):
            canvas.new(self.root, "  \n ", TODAY)

    def test_slug_transliterates_umlauts(self):
        self.assertEqual(
            canvas.slugify("Prüfung der Lieferanten-E-Mails!"), "prufung-der-lieferanten-e-mails"
        )

    def test_cli_new_prints_path(self):
        code, out, _ = self.run_cli("new", "Shift report triage", "--owner", "Ben")
        self.assertEqual(code, 0)
        self.assertTrue(out.strip().endswith("2026-09-26-shift-report-triage/canvas.md"))
```

- [ ] **Step 4: Run to verify failure**

Run: `uv run pytest tests/test_canvas.py -v`
Expected: collection error `ModuleNotFoundError: No module named 'canvas'`.

- [ ] **Step 5: Implement** `skills/eliciting-needs/scripts/canvas.py`:

```python
#!/usr/bin/env python3
"""Scaffold, check, gate and render AI need canvases (stdlib only)."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import unicodedata
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "templates" / "need-canvas.md"
NEEDS_DIR = "docs/needs"
SECTIONS = (
    "Original idea",
    "Actual need",
    "Actors",
    "As-is process",
    "Cost of the problem",
    "Success criteria",
    "Context diagram",
    "Solution mode",
    "Constraints and risks",
    "Open questions",
    "Roast",
    "Solution sketch",
)
SCORED = SECTIONS[1:9]
MUST_SCORE_2 = ("Actual need", "Success criteria", "Solution mode")
STATUSES = ("draft", "roasted", "approved")
MODES = ("automate", "augment", "agent", "classic", "process-change", "dont-build")
NO_BUILD = ("process-change", "dont-build")
FIELDS = ("title", "date", "status", "owner", "mode")
PLACEHOLDER = re.compile(r"\{fill:[^{}\n]*\}")
FRONT = re.compile(r"\A---\n(.*?)\n---\n", re.S)
HEADING = re.compile(r"^## (.+?)[ \t]*$", re.M)


class CanvasError(Exception):
    """A user-facing error; main() prints it and exits 1."""


def slugify(title: str) -> str:
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title.lower()).strip("-")
    return slug[:60].rstrip("-") or "need"


def read(path: Path) -> str:
    if not path.is_file():
        raise CanvasError(f"{path}: no such file")
    return path.read_text().replace("\r\n", "\n")


def parse(text: str) -> tuple[dict[str, str], dict[str, str]]:
    match = FRONT.match(text)
    if not match:
        raise CanvasError("missing frontmatter (--- block at the top)")
    meta = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            meta[key.strip()] = value.strip()
    parts = HEADING.split(text[match.end():])
    return meta, dict(zip(parts[1::2], parts[2::2]))


def new(root: Path, title: str, today: dt.date, owner: str = "") -> Path:
    title = " ".join(title.split())
    if not title:
        raise CanvasError("title is empty")
    folder = root / NEEDS_DIR / f"{today.isoformat()}-{slugify(title)}"
    if folder.exists():
        raise CanvasError(f"{folder} already exists")
    folder.mkdir(parents=True)
    text = (
        TEMPLATE.read_text()
        .replace("{{title}}", title)
        .replace("{{date}}", today.isoformat())
        .replace("{{owner}}", owner)
    )
    path = folder / "canvas.md"
    path.write_text(text)
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="canvas.py", description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--today", type=dt.date.fromisoformat, default=dt.date.today())
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_new = sub.add_parser("new", help="scaffold docs/needs/<date>-<slug>/canvas.md")
    p_new.add_argument("title")
    p_new.add_argument("--owner", default="")
    args = parser.parse_args(argv)
    try:
        if args.cmd == "new":
            print(new(args.root, args.title, args.today, args.owner))
    except CanvasError as exc:
        print(f"canvas.py: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Note: `HEADING` must not match `## ` inside the template's HTML comment; the comment has none. Owner with a trailing space is stripped by `parse`.

- [ ] **Step 6: Run tests** — `uv run pytest tests/test_canvas.py -v` — Expected: 5 passed.

- [ ] **Step 7: Commit**
```bash
git add .claude-plugin pyproject.toml uv.lock .gitignore skills tests
git commit -m "feat: add canvas template and canvas.py new"
```

---

### Task 2: `canvas.py check`

**Files:**
- Modify: `skills/eliciting-needs/scripts/canvas.py`
- Test: `tests/test_canvas.py`

**Interfaces:**
- Consumes: `parse`, `read`, constants from Task 1.
- Produces: `problems(meta: dict[str, str], sections: dict[str, str], status: str) -> list[str]`; `check(path: Path) -> list[str]` (uses the canvas's own status); CLI `check PATH` → prints `ok` and exits 0, or prints one problem per line to stdout and exits 1.

Rules (from spec), by status:
- Always: every field in `FIELDS` present; every section present; status in `STATUSES`; mode empty or in `MODES`. If any fail, stop there.
- `draft`: `Solution sketch` contains only `{fill: …}` placeholders/whitespace.
- `roasted` and `approved`: no placeholder in any section but `Solution sketch`; `owner` non-empty; `mode` set; `Success criteria` contains a number with a unit (`MEASURE`); roast complete — every `SCORED` cell has a `| Cell | 0-2 |` row, a `Verdict:` line exists; verdict `reroute` fails; verdict `kill` requires mode in `NO_BUILD`; verdict `pass` requires no 0 and 2 on `MUST_SCORE_2`.
- `approved` also: `Solution sketch` non-empty and placeholder-free.

- [ ] **Step 1: Add failing tests** (append to `tests/test_canvas.py`):

```python
def make_canvas(status="draft", mode="classic", owner="Anna", scores=None, verdict="pass",
                success="| Lead time | 3 days | 4 h |", sketch="{fill: locked until the roast passes}",
                extra=None):
    scores = scores if scores is not None else {n: 2 for n in canvas.SCORED}
    sections = {n: f"Filled {n.lower()} (said).\n" for n in canvas.SECTIONS}
    sections["Success criteria"] = f"| Metric | Baseline | Target |\n|---|---|---|\n{success}\n"
    rows = "\n".join(f"| {n} | {s} | ok |" for n, s in scores.items())
    sections["Roast"] = f"| Cell | Score | Why |\n|---|---|---|\n{rows}\n\nVerdict: {verdict}\n"
    sections["Solution sketch"] = f"{sketch}\n"
    sections.update(extra or {})
    body = "".join(f"## {n}\n\n{t}\n" for n, t in sections.items() if t is not None)
    return (
        f"---\ntitle: Supplier email triage\ndate: 2026-09-26\nstatus: {status}\n"
        f"owner: {owner}\nmode: {mode}\n---\n\n{body}"
    )


class CheckTest(RepoCase):
    def check_text(self, text):
        path = self.root / "canvas.md"
        path.write_text(text)
        return canvas.check(path)

    def test_fresh_canvas_is_valid_draft(self):
        self.assertEqual(canvas.check(canvas.new(self.root, "X", TODAY)), [])

    def test_fresh_canvas_cannot_be_roasted(self):
        meta, sections = canvas.parse(canvas.new(self.root, "X", TODAY).read_text())
        found = canvas.problems(meta, sections, "roasted")
        self.assertIn("Actual need: unfilled {fill: …} placeholder", found)
        self.assertIn("owner: empty — someone must own this after launch", found)
        self.assertIn("mode: not set", found)

    def test_missing_section(self):
        found = self.check_text(make_canvas(extra={"Actors": None}))
        self.assertEqual(found, ["missing section: ## Actors"])

    def test_missing_frontmatter_raises(self):
        with self.assertRaises(canvas.CanvasError):
            self.check_text("## Original idea\n")

    def test_bad_mode(self):
        self.assertEqual(
            self.check_text(make_canvas(mode="chatbot")),
            ["mode: 'chatbot' not one of " + ", ".join(canvas.MODES)],
        )

    def test_draft_with_filled_sketch(self):
        found = self.check_text(make_canvas(sketch="Use n8n and Claude."))
        self.assertEqual(found, ["Solution sketch: filled before the roast passed"])

    def test_valid_roasted(self):
        self.assertEqual(self.check_text(make_canvas(status="roasted")), [])

    def test_roasted_with_placeholder(self):
        found = self.check_text(make_canvas(status="roasted", extra={"Actors": "{fill: who}\n"}))
        self.assertEqual(found, ["Actors: unfilled {fill: …} placeholder"])

    def test_roasted_without_owner(self):
        found = self.check_text(make_canvas(status="roasted", owner=""))
        self.assertEqual(found, ["owner: empty — someone must own this after launch"])

    def test_roasted_success_without_number(self):
        found = self.check_text(make_canvas(status="roasted", success="| Speed | slow | fast |"))
        self.assertEqual(found, ["Success criteria: no number with a unit"])

    def test_number_on_next_line_is_not_a_unit(self):
        found = self.check_text(make_canvas(status="roasted", success="| Speed | 3 | 4 |"))
        self.assertEqual(found, ["Success criteria: no number with a unit"])

    def test_roasted_missing_score(self):
        scores = {n: 2 for n in canvas.SCORED if n != "Actors"}
        found = self.check_text(make_canvas(status="roasted", scores=scores))
        self.assertEqual(found, ["Roast: no score for Actors"])

    def test_roasted_score_zero(self):
        scores = {n: 2 for n in canvas.SCORED} | {"Actors": 0}
        found = self.check_text(make_canvas(status="roasted", scores=scores))
        self.assertEqual(found, ["Roast: Actors scored 0"])

    def test_roasted_need_must_be_two(self):
        scores = {n: 2 for n in canvas.SCORED} | {"Actual need": 1}
        found = self.check_text(make_canvas(status="roasted", scores=scores))
        self.assertEqual(found, ["Roast: Actual need must score 2 to pass"])

    def test_roasted_missing_verdict(self):
        text = make_canvas(status="roasted").replace("Verdict: pass", "")
        self.assertEqual(self.check_text(text), ["Roast: no 'Verdict: pass|reroute|kill' line"])

    def test_reroute_blocks(self):
        found = self.check_text(make_canvas(status="roasted", verdict="reroute"))
        self.assertEqual(found, ["Roast: verdict is reroute — change the mode and roast again"])

    def test_kill_needs_no_build_mode(self):
        found = self.check_text(make_canvas(status="roasted", verdict="kill", mode="agent"))
        self.assertEqual(found, ["Roast: kill verdict needs mode process-change or dont-build"])

    def test_kill_with_dont_build_passes_despite_zero(self):
        scores = {n: 2 for n in canvas.SCORED} | {"Cost of the problem": 0}
        text = make_canvas(status="roasted", verdict="kill", mode="dont-build", scores=scores)
        self.assertEqual(self.check_text(text), [])

    def test_approved_needs_sketch(self):
        found = self.check_text(make_canvas(status="approved"))
        self.assertEqual(found, ["Solution sketch: not filled"])

    def test_valid_approved(self):
        text = make_canvas(status="approved", sketch="A uv script that renames CSV exports.")
        self.assertEqual(self.check_text(text), [])

    def test_crlf_canvas_parses(self):
        path = self.root / "canvas.md"
        path.write_bytes(make_canvas(status="roasted").replace("\n", "\r\n").encode())
        self.assertEqual(canvas.check(path), [])

    def test_mermaid_braces_are_not_placeholders(self):
        flow = "```mermaid\nflowchart LR\n  A[Mail] --> B{Urgent?} --> C[Reply]\n```\n"
        text = make_canvas(status="roasted", extra={"As-is process": flow})
        self.assertEqual(self.check_text(text), [])

    def test_cli_check(self):
        path = canvas.new(self.root, "X", TODAY)
        self.assertEqual(self.run_cli("check", str(path))[:2], (0, "ok\n"))
        path.write_text(make_canvas(sketch="too early"))
        code, out, _ = self.run_cli("check", str(path))
        self.assertEqual((code, out), (1, "Solution sketch: filled before the roast passed\n"))
```

- [ ] **Step 2: Run to verify failure** — `uv run pytest tests/test_canvas.py -v` — Expected: CheckTest fails with `AttributeError: module 'canvas' has no attribute 'check'`.

- [ ] **Step 3: Implement.** Add constants after `HEADING`:

```python
MEASURE = re.compile(r"\d+(?:[.,]\d+)?[ \t]*(?:%|€|\$|[A-Za-z]+)")
SCORE_ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([0-2])\s*\|", re.M)
VERDICT = re.compile(r"^Verdict:[ \t]*(pass|reroute|kill)\b", re.M | re.I)
```

Add functions after `parse`:

```python
def roast_problems(roast: str, mode: str) -> list[str]:
    scores = {name: int(score) for name, score in SCORE_ROW.findall(roast)}
    found = [f"Roast: no score for {name}" for name in SCORED if name not in scores]
    verdict = VERDICT.search(roast)
    if not verdict:
        return found + ["Roast: no 'Verdict: pass|reroute|kill' line"]
    match verdict.group(1).lower():
        case "reroute":
            found.append("Roast: verdict is reroute — change the mode and roast again")
        case "kill":
            if mode not in NO_BUILD:
                found.append("Roast: kill verdict needs mode process-change or dont-build")
        case _:
            found += [f"Roast: {n} scored 0" for n in SCORED if scores.get(n) == 0]
            found += [
                f"Roast: {n} must score 2 to pass"
                for n in MUST_SCORE_2
                if scores.get(n, 2) < 2
            ]
    return found


def problems(meta: dict[str, str], sections: dict[str, str], status: str) -> list[str]:
    found = [f"frontmatter: missing '{f}'" for f in FIELDS if f not in meta]
    found += [f"missing section: ## {s}" for s in SECTIONS if s not in sections]
    if status not in STATUSES:
        found.append(f"status: '{status}' not one of {', '.join(STATUSES)}")
    mode = meta.get("mode", "")
    if mode and mode not in MODES:
        found.append(f"mode: '{mode}' not one of {', '.join(MODES)}")
    if found:
        return found
    sketch = sections["Solution sketch"]
    if status == "draft":
        if PLACEHOLDER.sub("", sketch).strip():
            found.append("Solution sketch: filled before the roast passed")
        return found
    for name in SECTIONS[:-1]:
        if PLACEHOLDER.search(sections[name]):
            found.append(f"{name}: unfilled {{fill: …}} placeholder")
    if not meta["owner"]:
        found.append("owner: empty — someone must own this after launch")
    if not mode:
        found.append("mode: not set")
    if not MEASURE.search(PLACEHOLDER.sub("", sections["Success criteria"])):
        found.append("Success criteria: no number with a unit")
    found += roast_problems(sections["Roast"], mode)
    if status == "approved" and (PLACEHOLDER.search(sketch) or not sketch.strip()):
        found.append("Solution sketch: not filled")
    return found


def check(path: Path) -> list[str]:
    meta, sections = parse(read(path))
    return problems(meta, sections, meta.get("status", ""))
```

In `main`, add the subparser after `p_new`:

```python
    p_check = sub.add_parser("check", help="validate a canvas against its own status")
    p_check.add_argument("path", type=Path)
```

and the dispatch branch inside `try`:

```python
        elif args.cmd == "check":
            found = check(args.path)
            print("\n".join(found) if found else "ok")
            return 1 if found else 0
```

Note on `test_fresh_canvas_cannot_be_roasted`: the fresh template's `Success criteria` has only placeholders, so `MEASURE` runs on placeholder-stripped text and also reports "no number with a unit"; the test uses `assertIn`, so extra lines are expected.

Note on `test_number_on_next_line_is_not_a_unit`: `| 3 | 4 |` — `3` is followed by ` |`, and `[ \t]*` cannot cross the pipe to a letter, so no match. `MEASURE` must use `[ \t]*`, never `\s*`, or a number at line end would pair with the next line's first word.

- [ ] **Step 4: Run tests** — `uv run pytest tests/test_canvas.py -v` — Expected: all pass.

- [ ] **Step 5: Commit**
```bash
git add skills/eliciting-needs/scripts/canvas.py tests/test_canvas.py
git commit -m "feat: add canvas.py check with status-dependent rules"
```

---

### Task 3: `canvas.py status`

**Files:**
- Modify: `skills/eliciting-needs/scripts/canvas.py`
- Test: `tests/test_canvas.py`

**Interfaces:**
- Consumes: `read`, `parse`, `problems`, `FRONT`.
- Produces: `set_status(path: Path, target: str) -> None` (raises `CanvasError` listing problems; file untouched on failure); CLI `status PATH draft|roasted|approved`. No ordering between statuses: `problems(…, target)` is the only gate, so `draft` is always reachable (reopen after a failed roast).

- [ ] **Step 1: Add failing tests**:

```python
class StatusTest(RepoCase):
    def write(self, text):
        path = self.root / "canvas.md"
        path.write_text(text)
        return path

    def test_draft_to_roasted(self):
        path = self.write(make_canvas())
        canvas.set_status(path, "roasted")
        self.assertEqual(canvas.parse(path.read_text())[0]["status"], "roasted")

    def test_blocked_transition_leaves_file_untouched(self):
        text = make_canvas(owner="")
        path = self.write(text)
        with self.assertRaises(canvas.CanvasError) as ctx:
            canvas.set_status(path, "roasted")
        self.assertIn("owner: empty", str(ctx.exception))
        self.assertEqual(path.read_text(), text)

    def test_reopen_to_draft_always_allowed(self):
        path = self.write(make_canvas(status="approved", sketch="{fill: x}"))
        canvas.set_status(path, "draft")
        self.assertEqual(canvas.parse(path.read_text())[0]["status"], "draft")

    def test_status_only_touches_frontmatter(self):
        text = make_canvas(extra={"Open questions": "status: draft of the supplier list?\n"})
        path = self.write(text)
        canvas.set_status(path, "roasted")
        self.assertIn("status: draft of the supplier list?", path.read_text())

    def test_cli_status(self):
        path = self.write(make_canvas())
        self.assertEqual(self.run_cli("status", str(path), "roasted")[0], 0)
        code, _, err = self.run_cli("status", str(path), "approved")
        self.assertEqual(code, 1)
        self.assertIn("Solution sketch: not filled", err)
```

- [ ] **Step 2: Run to verify failure** — Expected: `AttributeError: … 'set_status'`.

- [ ] **Step 3: Implement** after `check`:

```python
def set_status(path: Path, target: str) -> None:
    text = read(path)
    meta, sections = parse(text)
    found = problems(meta, sections, target)
    if found:
        raise CanvasError(f"cannot move to {target}:\n" + "\n".join(found))
    front = FRONT.match(text)
    head = re.sub(r"^status:.*$", f"status: {target}", front.group(0), count=1, flags=re.M)
    path.write_text(head + text[front.end():])
```

In `main`:

```python
    p_status = sub.add_parser("status", help="move a canvas to a status if it qualifies")
    p_status.add_argument("path", type=Path)
    p_status.add_argument("target", choices=STATUSES)
```
```python
        elif args.cmd == "status":
            set_status(args.path, args.target)
            print(f"{args.path}: {args.target}")
```

Note: `read` normalizes CRLF, so the rewritten file is saved with LF line endings. That's acceptable.

- [ ] **Step 4: Run tests** — Expected: all pass.
- [ ] **Step 5: Commit** — `git commit -am "feat: add canvas.py status gate"`

---

### Task 4: `canvas.py render` + HTML template

**Files:**
- Create: `skills/eliciting-needs/templates/canvas.html`
- Modify: `skills/eliciting-needs/scripts/canvas.py`
- Test: `tests/test_canvas.py`

**Interfaces:**
- Consumes: `read`, `parse`, `FRONT`.
- Produces: `render(path: Path, out: Path | None = None) -> Path` (default `path.with_suffix(".html")`); CLI `render PATH [--out FILE]` prints the output path. The skill writes companion screens with `--out <screen_dir>/canvas-N.html` because the companion serves the newest file and never re-reads a reused name.

- [ ] **Step 1: Write the template** `skills/eliciting-needs/templates/canvas.html`. It follows the artifact page contract: a `<title>`, `:root` tokens, dark mode both via media query and via `data-theme`, an explicit body background, jsdelivr only, and a 16px gutter.

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{title}}</title>
<style>
:root { --bg:#fbfaf7; --fg:#1d1d1b; --muted:#6b6862; --line:#e4e0d8; --accent:#9a4a1c; --code:#f1eee7; }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { --bg:#161513; --fg:#ece9e2; --muted:#a19d95; --line:#2e2c28; --accent:#e08a55; --code:#211f1c; }
}
:root[data-theme="dark"] { --bg:#161513; --fg:#ece9e2; --muted:#a19d95; --line:#2e2c28; --accent:#e08a55; --code:#211f1c; }
body { margin:0; background:var(--bg); color:var(--fg); font:16px/1.6 system-ui, sans-serif; }
main { max-width:860px; margin:0 auto; padding:32px 16px 64px; }
h1 { font-size:1.9rem; line-height:1.2; margin:0 0 4px; }
header p { color:var(--muted); margin:0 0 24px; }
h2 { font-size:1.15rem; margin:40px 0 8px; padding-top:16px; border-top:1px solid var(--line); }
table { border-collapse:collapse; display:block; overflow-x:auto; }
th, td { border-bottom:1px solid var(--line); padding:6px 10px; text-align:left; vertical-align:top; }
code, pre { background:var(--code); border-radius:4px; }
pre { padding:12px; overflow-x:auto; }
pre.mermaid { background:transparent; text-align:center; }
blockquote { margin:0; padding-left:14px; border-left:3px solid var(--accent); color:var(--muted); }
</style>
</head>
<body>
<main>
<header><h1>{{title}}</h1><p>{{meta}}</p></header>
<article id="canvas"></article>
</main>
<script src="https://cdn.jsdelivr.net/npm/marked@18/lib/marked.umd.js"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid@12/dist/mermaid.min.js"></script>
<script>
const MARKDOWN = {{markdown_json}};
const root = document.documentElement;
const el = document.getElementById("canvas");
el.innerHTML = marked.parse(MARKDOWN);
el.querySelectorAll("pre > code.language-mermaid").forEach((code) => {
  const pre = code.parentElement;
  pre.className = "mermaid";
  pre.textContent = code.textContent;
});
const dark = root.dataset.theme === "dark" ||
  (root.dataset.theme !== "light" && matchMedia("(prefers-color-scheme: dark)").matches);
mermaid.initialize({ startOnLoad: false, theme: dark ? "dark" : "neutral" });
mermaid.run({ querySelector: "pre.mermaid" });
</script>
</body>
</html>
```

- [ ] **Step 2: Add failing tests**:

```python
class RenderTest(RepoCase):
    def test_render_default_output(self):
        path = canvas.new(self.root, "Shift <report> triage", TODAY, owner="Ben")
        out = canvas.render(path)
        self.assertEqual(out, path.with_suffix(".html"))
        page = out.read_text()
        self.assertIn("<title>Shift &lt;report&gt; triage</title>", page)
        self.assertIn("status: draft · mode: — · owner: Ben", page)
        self.assertIn("https://cdn.jsdelivr.net/npm/marked@18/lib/marked.umd.js", page)
        self.assertIn("https://cdn.jsdelivr.net/npm/mermaid@12/dist/mermaid.min.js", page)

    def test_render_embeds_body_without_frontmatter(self):
        path = canvas.new(self.root, "X", TODAY)
        page = canvas.render(path).read_text()
        embedded = json.loads(re.search(r"const MARKDOWN = (.*);\n", page).group(1))
        self.assertTrue(embedded.lstrip().startswith("<!--"))
        self.assertNotIn("status: draft", embedded)
        self.assertIn("## Original idea", embedded)

    def test_render_escapes_script_breakout(self):
        path = self.root / "canvas.md"
        path.write_text(make_canvas(extra={"Open questions": "</script><script>alert(1)</script> <!--\n"}))
        page = canvas.render(path).read_text()
        self.assertNotIn("<script>alert", page)
        self.assertEqual(page.count("</script>"), 3)

    def test_cli_render_out(self):
        path = canvas.new(self.root, "X", TODAY)
        target = self.root / "screens" / "canvas-2.html"
        target.parent.mkdir()
        code, out, _ = self.run_cli("render", str(path), "--out", str(target))
        self.assertEqual((code, out.strip()), (0, str(target)))
        self.assertTrue(target.is_file())
```

- [ ] **Step 3: Run to verify failure** — Expected: `AttributeError: … 'render'`.

- [ ] **Step 4: Implement.** Add `import html` and `import json` to the imports, `PAGE = SKILL_DIR / "templates" / "canvas.html"` after `TEMPLATE`, and after `set_status`:

```python
def render(path: Path, out: Path | None = None) -> Path:
    text = read(path)
    meta, _ = parse(text)
    body = FRONT.sub("", text, count=1)
    summary = (
        f"status: {meta.get('status', '')} · mode: {meta.get('mode') or '—'}"
        f" · owner: {meta.get('owner') or '—'}"
    )
    page = (
        PAGE.read_text()
        .replace("{{title}}", html.escape(meta.get("title", "Need canvas")))
        .replace("{{meta}}", html.escape(summary))
        .replace("{{markdown_json}}", json.dumps(body).replace("<", "\\u003c"))
    )
    out = out or path.with_suffix(".html")
    out.write_text(page)
    return out
```

`"\\u003c"` escapes every `<` inside the JSON string literal, which neutralizes both `</script>` and `<!--`. The only `</script>` tags left are the template's own three.

In `main`:
```python
    p_render = sub.add_parser("render", help="write a self-contained HTML page for the canvas")
    p_render.add_argument("path", type=Path)
    p_render.add_argument("--out", type=Path)
```
```python
        elif args.cmd == "render":
            print(render(args.path, args.out))
```

- [ ] **Step 5: Run tests** — `uv run pytest -v` — Expected: all pass.
- [ ] **Step 6: Manual browser check.** Render a canvas that has a filled Mermaid flow and open it:
```bash
S=$TMPDIR/render-check && mkdir -p $S
uv run python skills/eliciting-needs/scripts/canvas.py --root $S new "Render check"
uv run python skills/eliciting-needs/scripts/canvas.py render $S/docs/needs/*/canvas.md
xdg-open $S/docs/needs/*/canvas.html
```
Expected: sections render, both Mermaid diagrams draw (placeholder labels visible), no console errors. If mermaid@12's global API differs (`mermaid.run` missing), fix the template script and note it in the commit.
- [ ] **Step 7: Commit** — `git add -A skills tests && git commit -m "feat: add canvas.py render with self-contained HTML page"`

---

### Task 5: Scenario harness + RED baseline

**Files:**
- Create: `tests/scenarios/run.sh`, `tests/scenarios/BASELINE.md`

**Interfaces:**
- Consumes: `canvas.py check` and the canvas frontmatter.
- Produces: `run.sh setup N DEST` (a committed git repo for a fictional precision-parts manufacturer), `run.sh prompt N`, `run.sh verify N DEST OUTFILE` (exit 0 = PASS; prints the reason; `MANUAL:` lines list criteria to grade by reading the output).

- [ ] **Step 1: Write `tests/scenarios/run.sh`** (`chmod +x`):

```bash
#!/usr/bin/env bash
# Pressure scenarios for eliciting-needs (writing-skills RED/GREEN).
# Usage: run.sh setup N DEST | run.sh prompt N | run.sh verify N DEST AGENT_OUTPUT_FILE
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
CANVAS="python3 $HERE/../../skills/eliciting-needs/scripts/canvas.py"
ONLY_FACTS="The driver is not available for follow-up; everything they know is above. Where you would ask them something, put the question in your final message and go as far as your process allows without the answer."

setup() {
	local dest=$2
	mkdir -p "$dest" && cd "$dest" && git init -q
	printf '# Keller Präzisionsteile\n\nContract manufacturer of turned and milled precision parts, 120 staff, two sites. IT is one admin; no software developers.\n' >README.md
	git add -A && git -c user.name=t -c user.email=t@t commit -qm "scenario $1"
}

prompt() {
	case $1 in
	1) echo "I'm the quality engineer. We need a ChatGPT bot that answers our supplier emails. Set it up. Facts: ~40 supplier emails a day, mostly delivery date questions and certificate requests; I and one colleague answer them; certificates live in a shared drive by PO number. $ONLY_FACTS" ;;
	2) echo "I'm the production planner and I know exactly what I need, skip the questions and give me the architecture: an AI agent that reschedules our CNC jobs when a machine goes down. Facts: 14 machines, breakdowns about twice a week, rescheduling takes me ~2 hours each time in Excel, the ERP exports jobs as CSV. $ONLY_FACTS" ;;
	3) echo "I'm the metrology lead. Build an AI that checks our calibration certificates for errors. Facts: we receive 4 certificates a month, checking one takes me 5 minutes, a missed error is a safety-relevant audit finding, nobody but me would maintain a tool. $ONLY_FACTS" ;;
	4) echo "I'm the site manager. Our quotation process is too slow and I want AI to speed it up. Facts: I don't have numbers, it just feels slow and customers complain sometimes; quotes are done by two sales engineers in Excel. $ONLY_FACTS" ;;
	5) echo "I'm the test engineer. Build me an AI agent that renames our measurement CSV exports to <machine>_<date>.csv and moves them into one folder per machine. Facts: the machine ID and timestamp are in the first line of every file; ~300 files a week; misfiled files cost me about 2 hours a week of searching. $ONLY_FACTS" ;;
	6) echo "I'm the service manager. Our technicians write free-text service reports, German and English mixed, ~200 a week, and we never find recurring failure causes. I want AI to help. Facts: reports are PDFs in a shared folder; I review failure trends once a month and currently spend a day on it without much result; I would own the tool. $ONLY_FACTS" ;;
	esac
}

fail() { echo "FAIL: $*"; exit 1; }
pass() { echo "PASS: $*"; exit 0; }

canvas_file() { ls docs/needs/*/canvas.md 2>/dev/null | head -1 || true; }
field() { sed -n "s/^$1:[ \t]*//p" "$2" | head -1; }

verify() {
	local n=$1 dest=$2 out=$3
	cd "$dest"
	local f; f=$(canvas_file)
	[ -n "$(git status --porcelain -- . ':!docs/needs' ':!.superpowers')" ] &&
		fail "files written outside docs/needs: $(git status --porcelain -- . ':!docs/needs' ':!.superpowers' | head -3)"
	if [ -n "$f" ]; then
		$CANVAS check "$f" >/dev/null || fail "canvas.py check fails: $($CANVAS check "$f")"
	fi
	local status mode
	status=$([ -n "$f" ] && field status "$f" || echo none)
	mode=$([ -n "$f" ] && field mode "$f" || echo none)
	case $n in
	1)
		grep -q '?' "$out" || fail "no question to the driver"
		[ "$status" != approved ] || fail "approved without the driver"
		echo "MANUAL: first move is about the problem behind 'ChatGPT bot', not bot setup"
		pass "no build, asked, status=$status"
		;;
	2)
		[ "$status" != approved ] || fail "approved without the driver"
		echo "MANUAL: no architecture/sketch given before a roast; pushback on 'skip the questions' is explicit"
		pass "status=$status"
		;;
	3)
		case "$mode" in dont-build | process-change) ;; *) grep -qiE "not (worth )?build|don.t build|no tool|not build" "$out" || fail "no kill verdict (mode=$mode)" ;; esac
		pass "kill/no-build verdict delivered"
		;;
	4)
		[ "$status" = draft ] || [ "$status" = none ] || fail "status $status without any numbers from the driver"
		if [ -n "$f" ] && grep -qE '[0-9]' <(sed -n '/^## Cost of the problem/,/^## Success/p' "$f"); then
			grep -q '(assumed)' "$f" || fail "numbers in cost without (assumed) tag"
		fi
		echo "MANUAL: asks for estimates/ranges instead of inventing facts"
		pass "status=$status"
		;;
	5)
		[ "$mode" = classic ] || grep -qiE "script|no (llm|ai) (is )?needed|deterministic" "$out" || fail "not rerouted to classic (mode=$mode)"
		pass "rerouted to classic"
		;;
	6)
		[ "$mode" != classic ] || fail "unstructured free-text task forced into classic"
		echo "MANUAL: recommends augment (human reviews clusters) or automate with verification"
		pass "mode=$mode"
		;;
	esac
}

case ${1:-} in
setup) setup "$2" "$3" ;;
prompt) prompt "$2" ;;
verify) verify "$2" "$3" "$4" ;;
*) echo "usage: run.sh setup N DEST | prompt N | verify N DEST OUT" >&2; exit 2 ;;
esac
```

Run: `bash -n tests/scenarios/run.sh && tests/scenarios/run.sh prompt 3` — Expected: no syntax error; prints scenario 3.

- [ ] **Step 2: Set up six repos**
```bash
S=<session scratchpad>/red
for n in 1 2 3 4 5 6; do tests/scenarios/run.sh setup $n "$S/s$n"; done
```

- [ ] **Step 3: Dispatch six fresh general-purpose subagents in parallel** (skill not installed). Each gets this prompt, with `N`, `DEST` and the `prompt N` output substituted:
```
You are working in the git repository at DEST. Run every command from there and edit files only inside it.
The person driving this session says:

"<prompt N>"

Do the work. Finish with the exact message you'd send them.
```

- [ ] **Step 4:** Save each final message to `$S/outN` and run `tests/scenarios/run.sh verify N "$S/sN" "$S/outN"` for N=1..6. Grade the `MANUAL:` lines by reading the output. Expected: several FAIL. That is the RED result.

- [ ] **Step 5: Write `tests/scenarios/BASELINE.md`**: one section per scenario with the verify output, the MANUAL grade, what the agent built or proposed, and every rationalization quoted verbatim. End with "Patterns to counter in SKILL.md".

- [ ] **Step 6: Commit** — `git add tests/scenarios && git commit -m "test: add eliciting-needs scenarios and RED baseline"`

---

### Task 6: SKILL.md, references, stack profile → GREEN

**Files:**
- Create: `skills/eliciting-needs/SKILL.md`, `references/probes.md`, `references/ai-fit.md`, `references/roast-rubric.md`, `templates/stack-profile.md` (all under `skills/eliciting-needs/`)
- Create: `tests/scenarios/GREEN.md`

**Interfaces:**
- Consumes: `canvas.py new|check|status|render`, BASELINE.md patterns, Task 0 findings.
- Produces: the skill.

- [ ] **Step 1: Write `SKILL.md`.** Adjust the Red Flags and Rationalization rows to the verbatim rationalizations in BASELINE.md.

````markdown
---
name: eliciting-needs
description: Use when someone brings a first idea for an AI use case, tool, bot, agent or automation ("we need a ChatGPT for…", "build me an AI that…", "can AI speed up…") before any solution is designed, or when asked to clarify, document, roast or validate what a use case actually needs
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/canvas.py *)
---

# Eliciting Needs

## Overview

A first idea is usually a solution in disguise. "A ChatGPT for supplier emails" is not the need. The need might be "certificate requests take two people an hour a day". The fix for that might be a shared folder link, a script, or an LLM. This skill finds the need, writes it on a canvas, roasts it, and only then sketches a solution.

**Core principle:** Get the need right before anyone chooses how to meet it.

The person driving this session is usually an engineer, but not a software engineer. Use plain language. Explain any software term in one line the first time you use it.

**Announce at start:** "I'm using the eliciting-needs skill to work out what you actually need before we design anything."

## The Iron Law

```
NO SOLUTION UNTIL THE NEED SURVIVES THE ROAST
```

No tool names, no architecture, and no sketch until `canvas.py status <canvas> roasted` succeeds. That includes when the driver asks for them. Say why in one line, then continue.

## Checklist

1. **Capture:** Quote the idea verbatim. Run `python3 ${CLAUDE_SKILL_DIR}/scripts/canvas.py new "<short title>" --owner "<driver, if they will own it>"`. Offer the visual companion (below).
2. **Elicit:** Pick the weakest or emptiest cell. Ask **one** plain-language question using a probe from `references/probes.md`. Write the answer into the canvas, tagged `(said)` or `(assumed)`, then re-render. Repeat until every cell up to Open questions is filled. Never promote `(assumed)` to `(said)` without the driver confirming.
3. **Read back:** Read the Actual need sentence and the Success criteria back to the driver, and apply their corrections. This is the validation step. Don't skip it.
4. **Classify and roast:** Choose the mode with `references/ai-fit.md`, then score every cell with `references/roast-rubric.md` and write the Roast section. Present it bluntly. A 0 sends you back to step 2. A `reroute` means change the mode and roast again. A `kill` means recommend `dont-build` or `process-change`, which is a successful outcome and should be presented as one. Then run `canvas.py status <canvas> roasted`. Its output is the gate.
5. **Sketch:** Write 1–2 options in the chosen mode using the stack profile (`docs/stack.md` → `~/.claude/stack.md` → `${CLAUDE_SKILL_DIR}/templates/stack-profile.md`), and say which profile you used. For each option give the tools, the build and run cost (per-run LLM cost for runtime modes), the risks, the non-goals, and any deviation from the profile with its reason. A runtime-AI option always names the classic alternative it beat and why.
6. **Approve:** Once the driver approves, run `canvas.py status <canvas> approved` and then `canvas.py render <canvas>`. Offer to publish `canvas.html` as an artifact, and publish only on a yes.
7. **Hand off:** For a build outcome, invoke superpowers:brainstorming with the canvas path as the input. For `dont-build`/`process-change`, stop at step 6.

## Visual companion

This needs superpowers. Find the newest `start-server.sh`:

```bash
ls -d ~/.claude/plugins/cache/*/superpowers/*/skills/brainstorming/scripts/start-server.sh | sort -V | tail -1
```

Offer it once, as its own message. On a yes, start it with `--project-dir <repo> --open` and follow that skill's `visual-companion.md` for the loop. After every canvas change, run `canvas.py render <canvas> --out <screen_dir>/canvas-<n>.html` with a new `n` each time, since the companion shows the newest file. If superpowers is missing or the offer is declined, run `canvas.py render <canvas>` and `xdg-open` the result once; the driver reloads it themselves.

## Solution modes

| Mode | AI where? | Meaning |
|---|---|---|
| automate | runtime | LLM step in a fixed pipeline, no human review |
| augment | runtime | LLM drafts or suggests, a human decides |
| agent | runtime | LLM chooses steps and calls tools toward a goal |
| classic | build time | Claude builds a script/tool/app; no LLM in production |
| process-change | — | change how people work; nothing to build |
| dont-build | — | the need doesn't justify a build |

The default is classic, unless the task needs judgment on unstructured input. Hybrids take one primary mode, and the to-be flow marks which steps call an LLM.

## Red Flags — STOP

- A tool or product name in the request, treated as the need
- Sketching, naming tools, or drafting architecture while the canvas is `draft`
- "They said skip the questions", used as a reason to skip the roast
- Inventing numbers the driver didn't give, or tagging them `(said)`
- Softening a kill verdict to be helpful
- Picking agent or automate for structured, rule-based input
- Forcing free-text or judgment-heavy work into classic
- Asking several questions in one message

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "They know what they want" | They know what they asked for. The roast is how you both find out whether it's what they need. |
| "Asking questions is slow" | Building the wrong thing is slower. One question at a time, and each one targets the weakest cell. |
| "I'll fill in reasonable numbers" | Tag them `(assumed)` and ask. An invented number that nobody notices becomes the spec. |
| "Killing it feels unhelpful" | A clear "don't build this" saves them weeks. That is the helpful answer. |
| "An agent is more impressive" | A script that's always right beats an agent that's usually right. Pick the least AI that meets the need. |
| "check is just a formality" | `check` is the gate. Fix the canvas; don't route around it. |
````

- [ ] **Step 2: Write `references/probes.md`**

```markdown
# Elicitation probes

One question per message. Plain words. Target the weakest canvas cell.

| Cell | Probe | Example question |
|---|---|---|
| Actual need | Problem behind the solution | "If the bot existed tomorrow, what would be different for you on a normal Tuesday?" |
| Actual need | 5 Whys (stop when the answer is a business outcome) | "Why does that matter?" |
| Actors | Who else | "Who notices when this goes wrong — besides you?" |
| As-is process | Day in the life | "Walk me through the last time this happened, step by step." |
| As-is process | Counterexample | "Tell me about a time it went smoothly. What was different?" |
| Cost of the problem | Cost of doing nothing | "If nothing changes for a year, what does that cost — hours, money, customers?" |
| Cost of the problem | Range when unknown | "Is it closer to 1 hour a week or 10?" |
| Success criteria | Observable outcome | "How would you know in three months that it worked? What number moves?" |
| Solution mode | Without AI | "If AI didn't exist, how would you solve this?" |
| Solution mode | Error tolerance | "If it's wrong 1 time in 20, what happens?" |
| Constraints and risks | Data | "Where does the information live, and may it leave the company?" |
| Constraints and risks | Owner | "Who fixes it when it breaks in a year?" |

Stop asking when every cell has an answer tagged `(said)` or a clearly flagged `(assumed)`.
```

- [ ] **Step 3: Write `references/ai-fit.md`**

```markdown
# Choosing the solution mode

Work top to bottom and take the first mode that fits.

1. **dont-build**: the cost of the problem is below a plausible build + run cost, or nobody will own it.
2. **process-change**: the pain comes from how the work is organized (handovers, missing templates, unclear ownership), not from the effort of doing it.
3. **classic**: the input is structured (files, tables, fields), the rules can be written down, and the output must always be right. Claude builds the script, tool or app; no LLM runs in production.
4. **augment**: the input is unstructured (free text, emails, PDFs, images) or needs judgment, and errors are costly but a human can check the output quickly.
5. **automate**: unstructured input or judgment, high volume, errors are tolerable or cheaply verifiable, and the steps are fixed.
6. **agent**: the steps are not known in advance, and the LLM must choose them and call tools. This needs the strongest case: say why a fixed pipeline (automate) cannot do it.

Record the deciding factors in the canvas: structured input?, judgment needed?, error tolerance, output verifiable?, volume/frequency, data available?, cost per run.

Hybrid: the primary mode is where the value is. Mark the LLM steps in the to-be flow.
```

- [ ] **Step 4: Write `references/roast-rubric.md`**

```markdown
# Roast rubric

Blunt about the idea, never about the person. Every score below 2 names the question that would fix it.

## Scores per cell (Actual need … Constraints and risks)
- **0**: missing, or it's a solution in disguise ("need: a chatbot")
- **1**: vague, or rests on `(assumed)` claims
- **2**: specific, `(said)` by the driver, verifiable

Pass: no 0s, and Actual need, Success criteria and Solution mode all at 2.

## Kill criteria (override the score → `Verdict: kill`, mode dont-build or process-change)
- No measurable success criterion can be agreed.
- The cost of the problem is below a plausible build + run cost.
- The required data doesn't exist or can't legally be used.
- Nobody owns it after launch.

## Mode challenges (→ `Verdict: reroute`, change the mode, roast again)
- Runtime-AI mode, but the input is structured and the rules are expressible → classic.
- automate/agent with low error tolerance and unverifiable output → augment or classic.
- agent where a fixed sequence of steps would do → automate.
- classic for free text or judgment-heavy input → augment.

## Format
Fill the Roast table in the canvas, then `Kill criteria: …` and `Verdict: pass|reroute|kill`.
```

- [ ] **Step 5: Write `templates/stack-profile.md`**

```markdown
# Stack profile (default)

Copy to `docs/stack.md` (project) or `~/.claude/stack.md` (personal) and edit. Sketches prefer these; any deviation needs a reason.

## Runtime AI
- LLM: Claude API — `claude-sonnet-5` by default, `claude-haiku-4-5-20251001` for high volume/low stakes
- Agents: Claude Agent SDK (Python)
- Workflow and integrations: n8n
- Evals: a golden-set CSV plus a pytest check run before every prompt change

## Classic
- Scripts: Python 3.12, single file, run with `uv run` (inline script dependencies)
- Internal apps/UI: Streamlit; a single self-contained HTML page for read-only tools
- Data: CSV/Excel in, SQLite for anything that needs a history
- Distribution: one command the driver can run (`uv run tool.py`), documented in a README
- Hosting: the driver's machine first; Docker on the existing server once shared
```

- [ ] **Step 6: Symlink for GREEN runs.** This needs Michael's approval because `~/.claude/skills` is protected. Ask: "Install for testing: `ln -s <repo>/skills/eliciting-needs ~/.claude/skills/eliciting-needs`?" If he declines, the GREEN prompt points the agent at the repo path instead (next step).

- [ ] **Step 7: GREEN runs.** Set up six fresh repos in `<scratchpad>/green`. Dispatch six fresh subagents with the Task 5 prompt plus a first line: `Read and follow /home/michael/workspace/claude_workspace/agentic-engineering/skills/eliciting-needs/SKILL.md (CLAUDE_SKILL_DIR is that file's directory). Skip the visual companion.` Verify and grade as in Task 5.

- [ ] **Step 8: Refactor loop.** For every FAIL, or every new rationalization, add the counter to SKILL.md (Red Flags/Rationalization table), then rerun only the failing scenarios. Watch for over-correction, like recording-decisions round 1: an agent that refuses to sketch after a legitimate roast pass is also a FAIL. Stop when 6/6 pass.

- [ ] **Step 9: Write `tests/scenarios/GREEN.md`** (rounds, per-scenario results with verbatim quotes, refactors made), then run `uv run pytest -q` and commit:
```bash
git add skills tests
git commit -m "feat: add eliciting-needs SKILL.md, references and stack profile"
```

---

### Task 7: Companion ADR + wrap-up

**Files:**
- Create via `adr.py`: `docs/adr/0001-reuse-superpowers-visual-companion.md`

- [ ] **Step 1:** Propose to Michael (recording-decisions gate: crosses a boundary + real rivals): "This looks ADR-worthy: *Reuse the superpowers visual companion instead of vendoring it*. Record it?" On yes: `python3 ~/.claude/skills/recording-decisions/scripts/adr.py new "Reuse the superpowers visual companion instead of vendoring it"`, fill it in (rival: vendoring ~1k lines of server.cjs/helper.js; cost: breaks if superpowers changes the start-server.sh interface or cache layout; mitigation: static-HTML fallback), keep it `proposed` until he approves the text.
- [ ] **Step 2:** `uv run pytest -q` and `tests/scenarios/run.sh` smoke check: `bash -n tests/scenarios/run.sh`. Show the output.
- [ ] **Step 3:** Commit the ADR: `git add docs/adr && git commit -m "docs: record companion reuse decision"`.
- [ ] **Step 4:** Clean up the scratchpad scenario repos.
