import datetime as dt
import io
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

SCRIPTS = (
    Path(__file__).resolve().parent.parent.parent
    / "skills"
    / "recording-decisions"
    / "scripts"
)
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
            code = adr.main(
                ["--root", str(self.root), "--today", TODAY.isoformat(), *args]
            )
        return code, out.getvalue(), err.getvalue()


class TemplateTests(unittest.TestCase):
    def test_every_template_brace_token_is_a_known_placeholder(self):
        for name in ("adr-minimal.md", "adr-full.md"):
            text = (adr.SKILL_DIR / "templates" / name).read_text()
            tokens = set(
                re.findall(r"\{[^{}\n]+\}", text.replace("{{", "").replace("}}", ""))
            )
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
        self.assertEqual(
            adr.find_adr_dir(self.root), self.root / "doc/architecture/decisions"
        )


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
        self.assertIn(
            "| [0001](0001-use-postgres-for-event-storage.md) | Use Postgres for event storage | proposed |",
            readme,
        )

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
        self.write(
            "doc/architecture/decisions/templates/template.md",
            "# NUMBER. TITLE\n\nDate: DATE\n\n## Status\n\nSTATUS\n\n## Context\n\n## Decision\n\n## Consequences\n",
        )
        self.write(
            "doc/architecture/decisions/0001-record-architecture-decisions.md",
            "# 1. Record architecture decisions\n\nDate: 2020-01-01\n\n## Status\n\nAccepted\n",
        )
        _, out, _ = self.run_cli("new", "Use gRPC between services")
        text = Path(out.strip()).read_text()
        self.assertTrue(
            out.strip().endswith(
                "doc/architecture/decisions/0002-use-grpc-between-services.md"
            )
        )
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
        self.assertIn(
            "Use A \\| B hybrid", (self.root / "docs/adr/README.md").read_text()
        )


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
        self.write("docs/adr/0002-b.md", madr("B", status="proposed", body="\n".join(f"line {i}" for i in range(70))))
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


class ReviewFixTests(RepoCase):
    def test_prose_mentioning_supersedes_does_not_link(self):
        self.write("docs/adr/0001-a.md", madr("A"))
        self.write("docs/adr/0002-b.md", madr("B", status="proposed", body="Kafka supersedes 1 nightly batch job."))
        code, _, err = self.run_cli("accept", "2")
        self.assertEqual(code, 0, err)
        self.assertEqual(adr.get_status((self.root / "docs/adr/0001-a.md").read_text()), "accepted")

    def test_status_cell_pipe_escaped(self):
        self.write(".adr-dir", "doc/adr\n")
        self.write("doc/adr/0001-x.md", "# 1. X\n\n## Status\n\nSuperseded by [2. Use A | B](0002-use-a-b.md)\n")
        self.write("doc/adr/0002-use-a-b.md", "# 2. Use A | B\n\n## Status\n\nAccepted\n\nSupersedes [1. X](0001-x.md)\n")
        rows = adr.render_index(self.root / "doc/adr").splitlines()[2:]
        for row in rows:
            self.assertEqual(len(re.split(r"(?<!\\)\|", row)), 5, row)

    def test_line_cap_skips_decided_adrs(self):
        self.write("docs/adr/0001-a.md", madr("A", body="\n".join(f"line {i}" for i in range(70))))
        adr.write_index(self.root / "docs/adr")
        self.assertEqual(adr.check(self.root / "docs/adr"), [])


if __name__ == "__main__":
    unittest.main()
