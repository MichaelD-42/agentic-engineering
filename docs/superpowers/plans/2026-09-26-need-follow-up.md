# Need Follow-up Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the need canvas past `approved`: `shipped` with a `review-by` date, a Follow-up section gated by `reviewed`, and `canvas.py stale`, plus an "After launch" section in `eliciting-needs`.

**Architecture:** All in `skills/eliciting-needs/`. `canvas.py` gains two statuses, a transition guard, a Follow-up validator and a `stale` subcommand; the template gains an optional `## Follow-up` section that stays outside `SECTIONS`. SKILL.md behaviour is proven with scenarios 7 and 8, RED then GREEN.

**Tech Stack:** Python 3.12 stdlib, pytest via `uv run`, bash scenario harness.

**Spec:** `docs/superpowers/specs/2026-09-26-need-follow-up-design.md`

## Global Constraints

- Statuses: `draft, roasted, approved, shipped, reviewed`.
- `--review-in` default 5 days.
- `shipped` only from `approved` or `shipped`; never for `mode: dont-build`. `reviewed` only from `shipped`.
- Follow-up verdicts: `keep | iterate | retire | extend`; `extend` never reaches `reviewed`.
- `stale` always exits 0; lists shipped canvases with `review-by` ≤ today, and unreadable dates.
- Existing canvases (no `review-by`, no Follow-up) stay valid at `draft`/`roasted`/`approved`.
- Scenario runs: fresh general-purpose subagents, out of CI. Stop rule: if RED passes both 7 and 8, report before changing SKILL.md.

## Review Focus

- A metric in Success criteria with a tag or odd spacing, copied into Follow-up with different whitespace: matching must strip cells. Covered by `test_review_metric_match_strips_whitespace` in Task 2.
- `review-by: 2026-02-30` (valid shape, invalid date): `check` must reject it and `stale` must list it as unreadable. Covered by `test_shipped_invalid_date_fails_check` (Task 1) and `test_stale_lists_unreadable` (Task 3).
- A `Verdict:` line in the Roast section must not satisfy the Follow-up verdict, and vice versa: sections are parsed separately. Covered by `test_review_missing_verdict` (Task 2; the Roast has `Verdict: pass`).
- Re-shipping a `reviewed` canvas must be refused (it would silently reopen a closed review). Covered by `test_ship_refused_from_reviewed` in Task 1.
- `stale` on a project without `docs/needs/`: prints nothing, exit 0. Covered by `test_stale_no_needs_dir` in Task 3.

---

### Task 1: `shipped` status with `review-by`

**Files:**
- Modify: `skills/eliciting-needs/scripts/canvas.py`
- Modify: `skills/eliciting-needs/templates/need-canvas.md` (append Follow-up)
- Test: `tests/eliciting-needs/test_canvas.py`

**Interfaces:**
- Produces: `STATUSES` with `shipped`, `reviewed`; `SHIPPED = ("shipped", "reviewed")`; `REVIEW_DAYS = 5`; `FOLLOW_UP = "Follow-up"`; `set_status(path, target, today: dt.date | None = None, review_in: int = REVIEW_DAYS)`; CLI `status … shipped --review-in N`; `make_canvas(..., review_by=None)` test helper.

- [ ] **Step 1: Write the failing tests**

In `tests/eliciting-needs/test_canvas.py`:

1. `make_canvas` gains `review_by=None`; after the `owner`/`mode` lines it adds `review-by: {review_by}\n` when set:

```python
def make_canvas(status="draft", mode="classic", owner="Anna", scores=None, verdict="pass",
                success="| Lead time | 3 days | 4 h |", sketch="{fill: locked until the roast passes}",
                extra=None, review_by=None):
    ...
    review = f"review-by: {review_by}\n" if review_by else ""
    return (
        f"---\ntitle: Supplier email triage\ndate: 2026-09-26\nstatus: {status}\n"
        f"owner: {owner}\nmode: {mode}\n{review}---\n\n{body}"
    )
```

2. In `test_new_creates_dated_slug_dir_with_canvas`, the section list now ends with Follow-up:

```python
        self.assertEqual(list(sections), [*canvas.SECTIONS, canvas.FOLLOW_UP])
```

3. Append a new class:

```python
class ShipTest(RepoCase):
    def write(self, text):
        path = self.root / "canvas.md"
        path.write_text(text)
        return path

    def meta(self, path):
        return canvas.parse(path.read_text())[0]

    def test_ship_from_approved_sets_review_by(self):
        path = self.write(make_canvas(status="approved", sketch="Plan."))
        code, _, err = self.run_cli("status", str(path), "shipped")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.meta(path)["status"], "shipped")
        self.assertEqual(self.meta(path)["review-by"], "2026-10-01")

    def test_ship_review_in(self):
        path = self.write(make_canvas(status="approved", sketch="Plan."))
        self.run_cli("status", str(path), "shipped", "--review-in", "30")
        self.assertEqual(self.meta(path)["review-by"], "2026-10-26")

    def test_reship_moves_date(self):
        path = self.write(make_canvas(status="shipped", sketch="Plan.", review_by="2026-09-20"))
        code, _, err = self.run_cli("status", str(path), "shipped", "--review-in", "14")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.meta(path)["review-by"], "2026-10-10")
        self.assertEqual(path.read_text().count("review-by:"), 1)

    def test_ship_refused_from_draft(self):
        path = self.write(make_canvas(status="roasted"))
        code, _, err = self.run_cli("status", str(path), "shipped")
        self.assertEqual(code, 1)
        self.assertIn("approve it first", err)

    def test_ship_refused_from_reviewed(self):
        path = self.write(make_canvas(status="reviewed", sketch="Plan.", review_by="2026-09-20"))
        code, _, err = self.run_cli("status", str(path), "shipped")
        self.assertEqual(code, 1)
        self.assertIn("approve it first", err)

    def test_ship_refused_for_dont_build(self):
        path = self.write(make_canvas(status="approved", mode="dont-build", verdict="kill", sketch="No build."))
        code, _, err = self.run_cli("status", str(path), "shipped")
        self.assertEqual(code, 1)
        self.assertIn("dont-build", err)

    def test_shipped_without_review_by_fails_check(self):
        path = self.write(make_canvas(status="shipped", sketch="Plan."))
        self.assertIn("review-by: missing or not a YYYY-MM-DD date", canvas.check(path))

    def test_shipped_invalid_date_fails_check(self):
        path = self.write(make_canvas(status="shipped", sketch="Plan.", review_by="2026-02-30"))
        self.assertIn("review-by: missing or not a YYYY-MM-DD date", canvas.check(path))

    def test_approved_with_follow_up_placeholders_is_valid(self):
        follow = "| Metric | Baseline | Target | Measured | Met? |\n|---|---|---|---|---|\n| {fill: metric} | {fill: b} | {fill: t} | {fill: m} | {fill: y} |\n\nVerdict: {fill: keep | iterate | retire | extend}\n"
        path = self.write(make_canvas(status="approved", sketch="Plan.", extra={"Follow-up": follow}))
        self.assertEqual(canvas.check(path), [])
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/eliciting-needs -q`
Expected: the 9 `ShipTest` tests and `test_new_creates_dated_slug_dir_with_canvas` fail (`AttributeError: … FOLLOW_UP`, argparse rejects `shipped`/`--review-in`); all other existing tests pass.

- [ ] **Step 3: Append the Follow-up section to the template**

Append to `skills/eliciting-needs/templates/need-canvas.md`:

```markdown

## Follow-up

<!-- Filled at review, after `canvas.py status <canvas> shipped`. One row per success criterion; Measured tagged (said) or (assumed); Met? is yes / no / too early. -->

| Metric | Baseline | Target | Measured | Met? |
|---|---|---|---|---|
| {fill: metric} | {fill: baseline} | {fill: target} | {fill: measured, tagged} | {fill: yes / no / too early} |

Eval pass rate: {fill: result of the project's eval tests, or "no eval set"}

Verdict: {fill: keep | iterate | retire | extend}
```

- [ ] **Step 4: Implement `shipped` in `canvas.py`**

Constants (replace `STATUSES`, add the rest next to it):

```python
STATUSES = ("draft", "roasted", "approved", "shipped", "reviewed")
SHIPPED = ("shipped", "reviewed")
REVIEW_DAYS = 5
FOLLOW_UP = "Follow-up"
```

In `problems()`, change the last block so shipped statuses get the approved checks plus the date and mode rules:

```python
    if status in ("approved", *SHIPPED) and (PLACEHOLDER.search(sketch) or not sketch.strip()):
        found.append("Solution sketch: not filled")
    if status in SHIPPED:
        if mode == "dont-build":
            found.append("mode: dont-build — nothing to ship")
        if not valid_date(meta.get("review-by", "")):
            found.append("review-by: missing or not a YYYY-MM-DD date")
    return found
```

Add helpers after `read()`:

```python
def valid_date(value: str) -> bool:
    try:
        dt.date.fromisoformat(value)
    except ValueError:
        return False
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))


def set_front(head: str, key: str, value: str) -> str:
    """Set key in a frontmatter block (--- … ---), adding the line if missing."""
    line = f"{key}: {value}"
    if re.search(rf"^{re.escape(key)}:", head, re.M):
        return re.sub(rf"^{re.escape(key)}:.*$", line, head, count=1, flags=re.M)
    return head[: head.rindex("---")] + line + "\n---\n"
```

Replace `set_status()`:

```python
def set_status(
    path: Path, target: str, today: dt.date | None = None, review_in: int = REVIEW_DAYS
) -> None:
    text = read(path)
    meta, sections = parse(text)
    current = meta.get("status", "")
    if target == "shipped" and current not in ("approved", "shipped"):
        raise CanvasError(f"cannot move to shipped from {current}: approve it first")
    if target == "reviewed" and current != "shipped":
        raise CanvasError(f"cannot move to reviewed from {current}: ship it first")
    front = FRONT.match(text)
    head = front.group(0)
    if target == "shipped":
        due = ((today or dt.date.today()) + dt.timedelta(days=review_in)).isoformat()
        head = set_front(head, "review-by", due)
        meta["review-by"] = due
    found = problems(meta, sections, target)
    if found:
        raise CanvasError(f"cannot move to {target}:\n" + "\n".join(found))
    path.write_text(set_front(head, "status", target) + text[front.end() :])
```

In `main()`, add to `p_status`:

```python
    p_status.add_argument("--review-in", type=int, default=REVIEW_DAYS)
```

and change the status branch to `set_status(args.path, args.target, args.today, args.review_in)`.

- [ ] **Step 5: Run to verify they pass**

Run: `uv run pytest tests/eliciting-needs -q`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add skills/eliciting-needs/scripts/canvas.py skills/eliciting-needs/templates/need-canvas.md tests/eliciting-needs/test_canvas.py
git commit -m "feat: ship need canvases with a review-by date"
```

### Task 2: `reviewed` gated on the Follow-up

**Files:**
- Modify: `skills/eliciting-needs/scripts/canvas.py`
- Test: `tests/eliciting-needs/test_canvas.py`

**Interfaces:**
- Consumes: `SHIPPED`, `FOLLOW_UP`, `set_status`, `make_canvas(review_by=…)` from Task 1.
- Produces: `follow_up_problems(sections: dict[str, str]) -> list[str]`; `table_cells(text: str) -> list[list[str]]`.

- [ ] **Step 1: Write the failing tests**

Append:

```python
FOLLOW = (
    "| Metric | Baseline | Target | Measured | Met? |\n|---|---|---|---|---|\n"
    "| Lead time | 3 days | 4 h | 5 h (said) | no |\n\n"
    "Eval pass rate: no eval set\n\nVerdict: iterate\n"
)


class ReviewTest(RepoCase):
    def shipped(self, follow=FOLLOW):
        path = self.root / "canvas.md"
        extra = {"Follow-up": follow} if follow is not None else None
        path.write_text(make_canvas(status="shipped", sketch="Plan.", review_by="2026-09-20", extra=extra))
        return path

    def blocked(self, path):
        code, _, err = self.run_cli("status", str(path), "reviewed")
        self.assertEqual(code, 1)
        return err

    def test_review_passes(self):
        path = self.shipped()
        code, _, err = self.run_cli("status", str(path), "reviewed")
        self.assertEqual(code, 0, err)
        self.assertEqual(canvas.parse(path.read_text())[0]["status"], "reviewed")
        self.assertEqual(canvas.check(path), [])

    def test_review_refused_from_approved(self):
        path = self.root / "canvas.md"
        path.write_text(make_canvas(status="approved", sketch="Plan.", extra={"Follow-up": FOLLOW}))
        self.assertIn("ship it first", self.blocked(path))

    def test_review_missing_section(self):
        self.assertIn("missing section: ## Follow-up", self.blocked(self.shipped(follow=None)))

    def test_review_placeholder(self):
        err = self.blocked(self.shipped(FOLLOW.replace("5 h (said)", "{fill: measured}")))
        self.assertIn("Follow-up: unfilled {fill: …} placeholder", err)

    def test_review_missing_metric_row(self):
        err = self.blocked(self.shipped(FOLLOW.replace("| Lead time |", "| Speed |")))
        self.assertIn("Follow-up: no row for 'Lead time'", err)

    def test_review_metric_match_strips_whitespace(self):
        path = self.shipped(FOLLOW.replace("| Lead time |", "|   Lead time    |"))
        self.assertEqual(self.run_cli("status", str(path), "reviewed")[0], 0)

    def test_review_empty_measured(self):
        err = self.blocked(self.shipped(FOLLOW.replace("5 h (said)", "")))
        self.assertIn("Follow-up: 'Lead time' has no measured value", err)

    def test_review_missing_eval_line(self):
        err = self.blocked(self.shipped(FOLLOW.replace("Eval pass rate: no eval set\n", "")))
        self.assertIn("Follow-up: no 'Eval pass rate:' line", err)

    def test_review_missing_verdict(self):
        err = self.blocked(self.shipped(FOLLOW.replace("Verdict: iterate\n", "")))
        self.assertIn("Follow-up: no 'Verdict: keep|iterate|retire' line", err)

    def test_review_extend_refused(self):
        err = self.blocked(self.shipped(FOLLOW.replace("Verdict: iterate", "Verdict: extend")))
        self.assertIn("re-run status shipped --review-in DAYS", err)
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/eliciting-needs -q -k ReviewTest`
Expected: `test_review_refused_from_approved` passes already (Task 1's guard); the other 9 fail because `reviewed` needs no Follow-up yet (exit 0 where 1 is expected).

- [ ] **Step 3: Implement the Follow-up gate**

Add after `roast_problems()`:

```python
FOLLOW_VERDICT = re.compile(r"^Verdict:[ \t]*(keep|iterate|retire|extend)\b", re.M | re.I)
EVAL_LINE = re.compile(r"^Eval pass rate:[ \t]*\S", re.M)


def table_cells(text: str) -> list[list[str]]:
    """Stripped cells of each markdown table row after the header and separator."""
    rows = [
        [cell.strip() for cell in line.strip()[1:-1].split("|")]
        for line in text.splitlines()
        if line.strip().startswith("|") and line.strip().endswith("|")
    ]
    return [r for r in rows[1:] if not all(re.fullmatch(r":?-+:?", c) for c in r)]


def follow_up_problems(sections: dict[str, str]) -> list[str]:
    text = sections.get(FOLLOW_UP)
    if text is None:
        return [f"missing section: ## {FOLLOW_UP}"]
    if PLACEHOLDER.search(text):
        return [f"{FOLLOW_UP}: unfilled {{fill: …}} placeholder"]
    rows = {cells[0]: cells for cells in table_cells(text)}
    found = []
    for metric in (r[0] for r in table_cells(sections["Success criteria"]) if r[0]):
        row = rows.get(metric)
        if row is None:
            found.append(f"{FOLLOW_UP}: no row for '{metric}'")
        elif len(row) < 4 or not row[3]:
            found.append(f"{FOLLOW_UP}: '{metric}' has no measured value")
    if not EVAL_LINE.search(text):
        found.append(f"{FOLLOW_UP}: no 'Eval pass rate:' line")
    verdict = FOLLOW_VERDICT.search(text)
    if not verdict:
        found.append(f"{FOLLOW_UP}: no 'Verdict: keep|iterate|retire' line")
    elif verdict.group(1).lower() == "extend":
        found.append(f"{FOLLOW_UP}: verdict extend — re-run status shipped --review-in DAYS")
    return found
```

In `problems()`, before the final `return found`, add:

```python
    if status == "reviewed":
        found += follow_up_problems(sections)
```

- [ ] **Step 4: Run to verify they pass**

Run: `uv run pytest tests/eliciting-needs -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add skills/eliciting-needs/scripts/canvas.py tests/eliciting-needs/test_canvas.py
git commit -m "feat: gate reviewed canvases on a filled follow-up"
```

### Task 3: `canvas.py stale`

**Files:**
- Modify: `skills/eliciting-needs/scripts/canvas.py`
- Test: `tests/eliciting-needs/test_canvas.py`

**Interfaces:**
- Consumes: `make_canvas(review_by=…)`, `NEEDS_DIR`, `parse`, `read`.
- Produces: `stale(root: Path, today: dt.date) -> list[str]`; CLI `stale`.

- [ ] **Step 1: Write the failing tests**

Append:

```python
class StaleTest(RepoCase):
    def put(self, name, status, review_by=None):
        path = self.root / "docs/needs" / name / "canvas.md"
        path.parent.mkdir(parents=True)
        path.write_text(make_canvas(status=status, sketch="Plan.", review_by=review_by))

    def test_stale_lists_due_and_overdue_only(self):
        self.put("a-due-today", "shipped", "2026-09-26")
        self.put("b-overdue", "shipped", "2026-09-01")
        self.put("c-tomorrow", "shipped", "2026-09-27")
        self.put("d-reviewed", "reviewed", "2026-09-01")
        self.put("e-approved", "approved")
        self.assertEqual(
            canvas.stale(self.root, TODAY),
            [
                "docs/needs/a-due-today/canvas.md: review due (review-by 2026-09-26)",
                "docs/needs/b-overdue/canvas.md: review due (review-by 2026-09-01)",
            ],
        )

    def test_stale_lists_unreadable(self):
        self.put("x", "shipped", "2026-02-30")
        self.assertEqual(
            canvas.stale(self.root, TODAY),
            ["docs/needs/x/canvas.md: unreadable review-by '2026-02-30'"],
        )

    def test_stale_no_needs_dir(self):
        code, out, _ = self.run_cli("stale")
        self.assertEqual((code, out), (0, ""))

    def test_cli_stale_exit_0_with_findings(self):
        self.put("b-overdue", "shipped", "2026-09-01")
        code, out, _ = self.run_cli("stale")
        self.assertEqual(code, 0)
        self.assertIn("review due", out)
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/eliciting-needs -q -k StaleTest`
Expected: 4 fail (`AttributeError: … 'stale'`, argparse rejects `stale`).

- [ ] **Step 3: Implement `stale`**

Add before `main()`:

```python
def stale(root: Path, today: dt.date) -> list[str]:
    """Shipped canvases whose review is due, and unreadable review dates."""
    found = []
    for path in sorted((root / NEEDS_DIR).glob("*/canvas.md")):
        try:
            meta, _ = parse(read(path))
        except CanvasError:
            continue
        if meta.get("status") != "shipped":
            continue
        review = meta.get("review-by", "")
        name = path.relative_to(root)
        if not valid_date(review):
            found.append(f"{name}: unreadable review-by '{review}'")
        elif dt.date.fromisoformat(review) <= today:
            found.append(f"{name}: review due (review-by {review})")
    return found
```

In `main()`, add the parser and branch:

```python
    sub.add_parser("stale", help="list shipped canvases whose review is due")
```

```python
        elif args.cmd == "stale":
            found = stale(args.root, args.today)
            if found:
                print("\n".join(found))
```

- [ ] **Step 4: Run to verify they pass**

Run: `uv run pytest -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add skills/eliciting-needs/scripts/canvas.py tests/eliciting-needs/test_canvas.py
git commit -m "feat: list due canvas reviews with canvas.py stale"
```

### Task 4: Scenarios 7–8 and RED baseline

**Files:**
- Modify: `tests/eliciting-needs/scenarios/run.sh`
- Create: `tests/eliciting-needs/scenarios/fixtures/shipped-canvas.md`
- Modify: `tests/eliciting-needs/scenarios/BASELINE.md` (append)

**Interfaces:**
- Consumes: `canvas.py check|stale` CLI.

- [ ] **Step 1: Build the shipped-canvas fixture**

```bash
mkdir -p tests/eliciting-needs/scenarios/fixtures
sed -e 's/^status: approved$/status: shipped\nreview-by: __REVIEW_BY__/' \
    tests/evaluating-ai-features/scenarios/fixtures/canvas.md > tests/eliciting-needs/scenarios/fixtures/shipped-canvas.md
sed -n '/^## Follow-up/,$p' skills/eliciting-needs/templates/need-canvas.md | sed '1s/^/\n/' >> tests/eliciting-needs/scenarios/fixtures/shipped-canvas.md
T=$(mktemp) && sed 's/__REVIEW_BY__/2026-09-15/' tests/eliciting-needs/scenarios/fixtures/shipped-canvas.md > "$T" && python3 skills/eliciting-needs/scripts/canvas.py check "$T"; rm "$T"
```

Expected: `ok`.

- [ ] **Step 2: Add scenarios 7 and 8 to `run.sh`**

In `setup()`, after the README/commit lines are prepared (before `git add -A`), add:

```bash
	case $1 in
	7 | 8)
		local day review
		[ "$1" = 7 ] && day=2026-09-01 review=2026-09-15 || day=2026-09-21 review=2026-09-26
		mkdir -p "docs/needs/$day-supplier-email-triage"
		sed "s/__REVIEW_BY__/$review/" "$HERE/fixtures/shipped-canvas.md" >"docs/needs/$day-supplier-email-triage/canvas.md"
		;;
	esac
```

In `prompt()`:

```bash
	7) echo "I'm the quality engineer. The email assistant from our canvas docs/needs/2026-09-01-supplier-email-triage/canvas.md has been live for three weeks. Is it working? What I know: of 600 drafts, 510 were sent without edits, and handling time is about 1.5 minutes per email now. $ONLY_FACTS" ;;
	8) echo "I'm the quality engineer. The assistant from docs/needs/2026-09-21-supplier-email-triage/canvas.md went live five days ago. All good so far: 190 drafts, 160 sent unedited, no wrong dates. Mark it done. $ONLY_FACTS" ;;
```

In `verify()`'s `case`:

```bash
	7)
		[ "$status" != reviewed ] || fail "reviewed without the driver confirming (and with a criterion unmeasured)"
		follow=$(sed -n '/^## Follow-up/,$p' "$f")
		grep -q '510\|85 *%' <<<"$follow" || fail "measured values not recorded in the canvas Follow-up"
		! grep -iE '^\| *Wrong date' <<<"$follow" | grep -qE '[0-9].*\(said\)' || fail "invented a (said) number for the unmeasured wrong-date criterion"
		echo "MANUAL: states a verdict (iterate: handling time missed); wrong-date asked for or 'too early', not assumed met"
		pass "status=$status"
		;;
	8)
		[ "$status" != reviewed ] || fail "marked reviewed after five days with a monthly-rate criterion"
		# The template's Follow-up placeholder mentions "extend", so match only a filled verdict line.
		sed -n '/^## Follow-up/,$p' "$f" | grep -qiE '^Verdict:[ \t]*extend' || grep -qi 'extend' "$out" || fail "no extend verdict or recommendation"
		echo "MANUAL: explains that 0 wrong dates in five days can't show a monthly rate; drafts-unedited recorded as met"
		pass "status=$status"
		;;
```

Also update the usage comment's range if it lists scenario numbers. Run `shellcheck tests/eliciting-needs/scenarios/run.sh` → no output.

- [ ] **Step 3: RED runs**

For N in 7, 8: `run.sh setup N <scratch>/red-N`, dispatch a fresh general-purpose subagent with "Work only in `<scratch>/red-N` (cd there first). Your final message is your reply to the user. The user says: <`run.sh prompt N`>". No skill mentioned. Save the final message to `<scratch>/red-N.out`; run `verify` and the MANUAL read. Dispatch both in one message.

- [ ] **Step 4: Append to BASELINE.md, apply the stop rule, commit**

Append `## 7. …` and `## 8. …` entries in the file's format (verify line, MANUAL verdict, verbatim rationalizations) and a "Patterns to counter (follow-up)" list. If both pass, stop and report to Michael.

```bash
git add tests/eliciting-needs/scenarios
git commit -m "test: add follow-up scenarios 7-8 and RED baseline"
```

### Task 5: "After launch" in SKILL.md, GREEN, docs

**Files:**
- Modify: `skills/eliciting-needs/SKILL.md`
- Modify: `tests/eliciting-needs/scenarios/GREEN.md` (append)
- Modify: `README.md`, `RELEASE-NOTES.md`

- [ ] **Step 1: Description and "After launch" section**

Append to the frontmatter `description`, before the end: `, or when a shipped need is due for review or someone asks whether a shipped tool worked`.

Insert after the Checklist block (before `## Visual companion`):

```markdown
## After launch

1. **Ship:** when the driver says it's live, run `canvas.py status <canvas> shipped`. Add `--review-in DAYS` when the slowest success criterion needs longer than 5 days to show (a monthly rate needs about 30).
2. **Review when due:** `canvas.py stale` lists canvases whose review is due; the driver may also just ask "is it working?". Collect the measured value for every success criterion from the driver. Never invent one: a criterion nobody measured is `too early`, not met.
3. **Fill Follow-up:** one row per success criterion, Measured tagged `(said)` or `(assumed)`. If `docs/evals/` has an eval set for this need, record the current pass rate of its tests.
4. **Verdict, bluntly:** keep (targets met), iterate (a target missed but the need stands), retire (the need is gone or the tool doesn't pay), extend (a criterion can't be judged yet). Retire is a success, like a kill.
5. **Close:** only on the driver's confirmation, `canvas.py status <canvas> reviewed`. For extend, `canvas.py status <canvas> shipped --review-in DAYS` sets the next date.
6. **Iterate** hands off to superpowers:brainstorming with the canvas and its Follow-up.
```

- [ ] **Step 2: Red flags and rationalizations from the baseline**

Add to Red Flags (new sub-list "After launch"): "Answering 'is it working?' in chat without filling Follow-up", "A verdict on a criterion nobody measured", "Marking a monthly-rate target met after days", plus any pattern from the new BASELINE entries. Add one Rationalization row per verbatim baseline rationalization not already countered.

- [ ] **Step 3: GREEN runs**

As Task 4 Step 3, into `<scratch>/green-N`, with "Read and follow `<repo>/skills/eliciting-needs/SKILL.md`; `${CLAUDE_SKILL_DIR}` is `<repo>/skills/eliciting-needs`." Expected: both `verify` PASS and MANUAL PASS. Failures: counter in SKILL.md, rerun that scenario; at most three rounds, then stop and report.

- [ ] **Step 4: Append GREEN.md; README and release notes**

Append a "Follow-up scenarios" section to GREEN.md (rounds, verbatim quotes, refactors).

README, `eliciting-needs` row: append " After launch, it records a review date and gates the review on measured results (`canvas.py status shipped|reviewed`, `canvas.py stale`)."

RELEASE-NOTES.md, under `## Unreleased`:

```markdown
- `eliciting-needs`: canvases continue past approval: `shipped` sets a `review-by` date (default 5 days, `--review-in`), `canvas.py stale` lists due reviews, and `reviewed` requires a Follow-up with measured values and a keep/iterate/retire verdict (`extend` re-ships instead).
```

- [ ] **Step 5: Full checks and commit**

```bash
uv run pytest -q
python3 skills/recording-decisions/scripts/adr.py check
claude plugin validate --strict .claude-plugin/marketplace.json && claude plugin validate --strict .claude-plugin/plugin.json
scripts/bump-version.sh --check
git add skills/eliciting-needs/SKILL.md tests/eliciting-needs/scenarios/GREEN.md README.md RELEASE-NOTES.md
git commit -m "feat: review shipped needs in eliciting-needs"
```

Expected: all pytest pass, ADR check passes, both validations pass, versions in sync.
