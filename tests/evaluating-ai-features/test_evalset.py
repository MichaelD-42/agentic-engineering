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
