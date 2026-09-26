import datetime as dt
import io
import json
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

SCRIPTS = (
    Path(__file__).resolve().parent.parent.parent / "skills" / "eliciting-needs" / "scripts"
)
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
            code = canvas.main(
                ["--root", str(self.root), "--today", TODAY.isoformat(), *args]
            )
        return code, out.getvalue(), err.getvalue()


class NewTest(RepoCase):
    def test_new_creates_dated_slug_dir_with_canvas(self):
        path = canvas.new(self.root, "Supplier email triage", TODAY, owner="Anna")
        self.assertEqual(
            path, self.root / "docs/needs/2026-09-26-supplier-email-triage/canvas.md"
        )
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
            canvas.slugify("Prüfung der Lieferanten-E-Mails!"),
            "prufung-der-lieferanten-e-mails",
        )

    def test_cli_new_prints_path(self):
        code, out, _ = self.run_cli("new", "Shift report triage", "--owner", "Ben")
        self.assertEqual(code, 0)
        self.assertTrue(
            out.strip().endswith("2026-09-26-shift-report-triage/canvas.md")
        )


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

    def test_kill_without_measure_or_owner_passes(self):
        text = make_canvas(
            status="roasted",
            verdict="kill",
            mode="dont-build",
            owner="",
            success="| none agreed (said) | – | – |",
        )
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


    def test_render_escapes_raw_html_blocks(self):
        page = canvas.render(canvas.new(self.root, "X", TODAY)).read_text()
        self.assertIn("html(token)", page)
        self.assertIn('token.text.startsWith("<!--")', page)
