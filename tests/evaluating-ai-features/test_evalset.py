import csv
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

SCRIPTS = (
    Path(__file__).resolve().parent.parent.parent
    / "skills"
    / "evaluating-ai-features"
    / "scripts"
)
sys.path.insert(0, str(SCRIPTS))
import evalset  # noqa: E402

CANVAS = """---
title: Supplier email triage
date: 2026-09-20
status: approved
owner: QE
mode: augment
---

## Success criteria

| Metric | Baseline | Target |
|---|---|---|
| Drafts accepted without edits (said) | 0% | 80% |
| Wrong date/certificate sent (said) | 1 per month | 0 per month |
| {fill: metric} | {fill: today} | {fill: goal} |

## Solution mode

Mode: augment
"""


class RepoCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self):
        self._tmp.cleanup()

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = evalset.main(["--root", str(self.root), *args])
        return code, out.getvalue(), err.getvalue()

    def criteria(self, folder):
        meta, body = evalset.parse_front((folder / "plan.md").read_text())
        return evalset.table_rows(evalset.sections(body)["Criteria"])


class NewTest(RepoCase):
    def test_new_without_canvas_scaffolds_draft(self):
        folder = evalset.new(self.root, "Service report classifier")
        self.assertEqual(folder, self.root / "docs/evals/service-report-classifier")
        meta, _ = evalset.parse_front((folder / "plan.md").read_text())
        self.assertEqual(meta["name"], "Service report classifier")
        self.assertEqual(meta["status"], "draft")
        self.assertEqual(meta["canvas"], "")
        self.assertEqual(meta["k"], "3")
        self.assertEqual(self.criteria(folder), [["c1", "", "", ""]])
        with (folder / "cases.csv").open(newline="") as fh:
            self.assertEqual(list(csv.reader(fh)), [evalset.HEADER])

    def test_new_with_canvas_imports_filled_criteria(self):
        canvas = self.root / "docs/needs/x/canvas.md"
        canvas.parent.mkdir(parents=True)
        canvas.write_text(CANVAS)
        folder = evalset.new(self.root, "Supplier email triage", canvas)
        meta, _ = evalset.parse_front((folder / "plan.md").read_text())
        self.assertEqual(meta["canvas"], str(canvas))
        self.assertEqual(
            self.criteria(folder),
            [
                ["c1", "Drafts accepted without edits (said): 0% → 80%", "", ""],
                ["c2", "Wrong date/certificate sent (said): 1 per month → 0 per month", "", ""],
            ],
        )

    def test_new_with_canvas_escapes_pipes(self):
        canvas = self.root / "canvas.md"
        canvas.write_text(CANVAS.replace("Wrong date/certificate", "Wrong date \\| certificate"))
        folder = evalset.new(self.root, "Pipes", canvas)
        self.assertEqual(len(self.criteria(folder)), 2)

    def test_new_refuses_existing(self):
        evalset.new(self.root, "Twice")
        with self.assertRaises(evalset.EvalError):
            evalset.new(self.root, "Twice")

    def test_new_canvas_without_criteria_is_error(self):
        canvas = self.root / "canvas.md"
        canvas.write_text("---\ntitle: x\n---\n\n## Actual need\n\nx\n")
        with self.assertRaises(evalset.EvalError):
            evalset.new(self.root, "No criteria", canvas)

    def test_cli_new_prints_folder(self):
        code, out, _ = self.run_cli("new", "Cli made")
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), str(self.root / "docs/evals/cli-made"))


def write_valid(folder, cases=20, said=10, refuse=1):
    """A passing eval set: criteria c1, c2; cases alternate between them."""
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "plan.md").write_text(
        "---\nname: Valid\nstatus: draft\ncanvas: \nk: 3\n---\n\n## Criteria\n\n"
        "| id | criterion | grader | threshold |\n|---|---|---|---|\n"
        "| c1 | Right category | code | ≥ 95% pass all k |\n"
        "| c2 | Polite reply | model | ≥ 90% pass all k |\n\n## Grading notes\n\nx\n"
    )
    with (folder / "cases.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(evalset.HEADER)
        for n in range(cases):
            w.writerow([
                f"t{n}",
                "c1" if n % 2 == 0 else "c2",
                "said" if n < said else "assumed",
                "refuse" if n < refuse else "normal",
                f"input {n}",
                f"expected {n}",
                "code" if n % 2 == 0 else "model",
            ])
    return folder


def rewrite_cases(folder, edit):
    """Apply edit(rows) to the data rows of cases.csv."""
    with (folder / "cases.csv").open(newline="") as fh:
        rows = list(csv.reader(fh))
    header, data = rows[0], rows[1:]
    edit(header, data)
    with (folder / "cases.csv").open("w", newline="") as fh:
        csv.writer(fh).writerows([header, *data])


class CheckTest(RepoCase):
    def setUp(self):
        super().setUp()
        self.folder = write_valid(self.root / "docs/evals/valid")

    def problems(self):
        return "\n".join(evalset.check(self.folder))

    def test_valid_set_passes(self):
        self.assertEqual(evalset.check(self.folder), [])
        code, out, _ = self.run_cli("check", str(self.folder))
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "eval set OK (20 cases from 20 inputs, 10 real)")

    def test_rule1_bad_frontmatter(self):
        plan = self.folder / "plan.md"
        plan.write_text(plan.read_text().replace("status: draft", "status: done").replace("k: 3", "k: 0"))
        found = self.problems()
        self.assertIn("status", found)
        self.assertIn("k must be", found)

    def test_rule1_criterion_without_grader_or_threshold(self):
        plan = self.folder / "plan.md"
        plan.write_text(plan.read_text().replace("| code | ≥ 95% pass all k |", "|  |  |"))
        found = self.problems()
        self.assertIn("c1: grader", found)
        self.assertIn("c1: threshold", found)

    def test_rule2_wrong_header(self):
        rewrite_cases(self.folder, lambda h, d: h.__setitem__(0, "case"))
        self.assertIn("header", self.problems())

    def test_rule2_bad_values(self):
        def edit(h, d):
            d[0][1] = "c9"
            d[1][2] = "guessed"
            d[2][3] = "weird"
            d[3][6] = "human"
            d[4][5] = ""
            d[5][0] = d[6][0]
        rewrite_cases(self.folder, edit)
        found = self.problems()
        for fragment in ("unknown criterion c9", "source", "kind", "grader", "expected is empty", "duplicate id"):
            self.assertIn(fragment, found)

    def test_rule3_uncovered_criterion(self):
        def edit(h, d):
            for row in d:
                row[1] = "c1"
        rewrite_cases(self.folder, edit)
        self.assertIn("coverage: c2 has no cases", self.problems())

    def test_rule4_too_few_cases(self):
        write_valid(self.folder, cases=19, said=10)
        self.assertIn("count: 19 distinct inputs, need at least 20", self.problems())

    def test_rule5_too_few_said(self):
        write_valid(self.folder, cases=20, said=9)
        self.assertIn("said: 9 of 20 distinct inputs", self.problems())

    def test_rows_per_criterion_count_as_one_input(self):
        # 7 real inputs x 3 criteria = 21 rows: still only 7 examples.
        def edit(h, d):
            for n, row in enumerate(d):
                row[4] = f"input {n % 7}"
        rewrite_cases(self.folder, edit)
        found = self.problems()
        self.assertIn("count: 7 distinct inputs, need at least 20", found)

    def test_said_counts_distinct_inputs(self):
        # 10 said rows, but all the same email.
        def edit(h, d):
            for row in d[:10]:
                row[4] = "same email"
        rewrite_cases(self.folder, edit)
        self.assertIn("said: 1 of 11 distinct inputs", self.problems())

    def test_rule6_no_refuse(self):
        write_valid(self.folder, refuse=0)
        self.assertIn("refuse: no refuse case", self.problems())

    def test_excel_semicolon_bom_passes(self):
        with (self.folder / "cases.csv").open(newline="") as fh:
            rows = list(csv.reader(fh))
        buf = io.StringIO()
        csv.writer(buf, delimiter=";").writerows(rows)
        (self.folder / "cases.csv").write_bytes(("﻿" + buf.getvalue()).encode("utf-8"))
        self.assertEqual(evalset.check(self.folder), [])

    def test_multiline_input_is_one_case(self):
        rewrite_cases(self.folder, lambda h, d: d[0].__setitem__(4, "Hello,\nwhen is PO 4711 due?\nThanks"))
        self.assertEqual(evalset.check(self.folder), [])

    def test_blank_rows_ignored(self):
        with (self.folder / "cases.csv").open("a", newline="") as fh:
            fh.write(",,,,,,\r\n\r\n")
        self.assertEqual(evalset.check(self.folder), [])

    def test_cli_check_failure_exit_1(self):
        write_valid(self.folder, refuse=0)
        code, out, _ = self.run_cli("check", str(self.folder))
        self.assertEqual(code, 1)
        self.assertIn("refuse", out)


class StatusTest(RepoCase):
    def test_ready_blocked_by_failing_check(self):
        folder = write_valid(self.root / "e", refuse=0)
        code, _, err = self.run_cli("status", str(folder), "ready")
        self.assertEqual(code, 1)
        self.assertIn("refuse", err)
        meta, _ = evalset.parse_front((folder / "plan.md").read_text())
        self.assertEqual(meta["status"], "draft")

    def test_ready_allowed_and_only_status_changes(self):
        folder = write_valid(self.root / "e")
        before = (folder / "plan.md").read_text()
        code, _, _ = self.run_cli("status", str(folder), "ready")
        self.assertEqual(code, 0)
        after = (folder / "plan.md").read_text()
        self.assertEqual(after, before.replace("status: draft", "status: ready", 1))

    def test_check_flags_a_ready_set_that_no_longer_passes(self):
        folder = write_valid(self.root / "e")
        evalset.set_status(folder, "ready")
        self.assertEqual(evalset.check(folder), [])
        rewrite_cases(folder, lambda h, d: d[0].__setitem__(5, ""))
        self.assertIn("status is ready but the set no longer passes", "\n".join(evalset.check(folder)))

    def test_draft_always_allowed(self):
        folder = write_valid(self.root / "e", refuse=0)
        evalset.set_status(folder, "draft")
        meta, _ = evalset.parse_front((folder / "plan.md").read_text())
        self.assertEqual(meta["status"], "draft")
