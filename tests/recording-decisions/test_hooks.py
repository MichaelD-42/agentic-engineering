import json
import re
import tempfile
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_adr import SCRIPTS, RepoCase, adr, madr  # noqa: E402


class HookCase(RepoCase):
    def hook(self, script, tool_name, **tool_input):
        event = {
            "tool_name": tool_name,
            "tool_input": tool_input,
            "cwd": str(self.root),
        }
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / script)],
            input=json.dumps(event),
            capture_output=True,
            text=True,
        )
        return result.returncode, result.stderr

    def setUp(self):
        super().setUp()
        self.accepted = self.write("docs/adr/0001-a.md", madr("A"))
        self.proposed = self.write("docs/adr/0002-b.md", madr("B", status="proposed"))
        adr.write_index(self.root / "docs/adr")


class ImmutableTests(HookCase):
    def test_blocks_body_edit_of_accepted(self):
        code, err = self.hook(
            "hook_immutable.py",
            "Edit",
            file_path=str(self.accepted),
            old_string="Why.",
            new_string="Why not.",
        )
        self.assertEqual(code, 2)
        self.assertIn("supersede", err)

    def test_immutable_allows_status_and_review_by_edit(self):
        code, _ = self.hook(
            "hook_immutable.py",
            "Edit",
            file_path=str(self.accepted),
            old_string="status: accepted",
            new_string="status: deprecated",
        )
        self.assertEqual(code, 0)
        code, _ = self.hook(
            "hook_immutable.py",
            "Edit",
            file_path=str(self.accepted),
            old_string="review-by: 2027-09-26",
            new_string="review-by: 2028-09-26",
        )
        self.assertEqual(code, 0)

    def test_blocks_write_replacing_accepted_body(self):
        code, _ = self.hook(
            "hook_immutable.py",
            "Write",
            file_path=str(self.accepted),
            content=madr("A2"),
        )
        self.assertEqual(code, 2)

    def test_allows_proposed_edits(self):
        code, _ = self.hook(
            "hook_immutable.py",
            "Edit",
            file_path=str(self.proposed),
            old_string="Why.",
            new_string="Because.",
        )
        self.assertEqual(code, 0)

    def test_immutable_ignores_non_adr_files(self):
        for rel in (
            "docs/adr/README.md",
            "docs/adr/templates/template.md",
            "src/x.py",
            "docs/adr/0009-new.md",
        ):
            code, _ = self.hook(
                "hook_immutable.py", "Write", file_path=rel, content="x"
            )
            self.assertEqual(code, 0, rel)


class ValidateTests(HookCase):
    def test_reports_invalid_adr(self):
        self.proposed.write_text(madr("B", status="maybe"))
        adr.write_index(self.root / "docs/adr")
        code, err = self.hook(
            "hook_validate.py", "Write", file_path=str(self.proposed), content=""
        )
        self.assertEqual(code, 2)
        self.assertIn("invalid status 'maybe'", err)

    def test_passes_valid_adr(self):
        code, err = self.hook("hook_validate.py", "Edit", file_path=str(self.proposed))
        self.assertEqual((code, err), (0, ""))

    def test_readme_edit_runs_repo_checks_only(self):
        (self.root / "docs/adr/README.md").write_text("# Decisions\n")
        code, err = self.hook(
            "hook_validate.py", "Write", file_path=str(self.root / "docs/adr/README.md")
        )
        self.assertEqual(code, 2)
        self.assertIn("index missing", err)

    def test_validate_ignores_files_outside_adr_dir(self):
        code, err = self.hook("hook_validate.py", "Write", file_path="src/x.py")
        self.assertEqual((code, err), (0, ""))


class ForeignCwdTests(HookCase):
    """Session cwd is often a parent workspace, not the repo that holds the ADRs."""

    def hook_from(self, cwd, script, tool_name, **tool_input):
        event = {"tool_name": tool_name, "tool_input": tool_input, "cwd": str(cwd)}
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / script)],
            input=json.dumps(event),
            capture_output=True,
            text=True,
        )
        return result.returncode, result.stderr

    def test_immutable_blocks_when_cwd_is_elsewhere(self):
        code, _ = self.hook_from(
            "/",
            "hook_immutable.py",
            "Edit",
            file_path=str(self.accepted),
            old_string="Why.",
            new_string="Why not.",
        )
        self.assertEqual(code, 2)

    def test_validate_reports_when_cwd_is_elsewhere(self):
        self.proposed.write_text(madr("B", status="maybe"))
        adr.write_index(self.root / "docs/adr")
        code, _ = self.hook_from(
            "/", "hook_validate.py", "Write", file_path=str(self.proposed)
        )
        self.assertEqual(code, 2)


class GuardHardeningTests(HookCase):
    def test_blocks_regression_to_proposed(self):
        code, err = self.hook(
            "hook_immutable.py",
            "Edit",
            file_path=str(self.accepted),
            old_string="status: accepted",
            new_string="status: proposed",
        )
        self.assertEqual(code, 2)
        self.assertIn("proposed", err)

    def test_blocks_prose_in_date_field(self):
        code, _ = self.hook(
            "hook_immutable.py",
            "Edit",
            file_path=str(self.accepted),
            old_string="date: 2026-01-01",
            new_string="date: 2026 -- actually we chose MySQL",
        )
        self.assertEqual(code, 2)

    def test_blocks_edit_it_cannot_reproduce(self):
        code, err = self.hook(
            "hook_immutable.py",
            "Edit",
            file_path=str(self.accepted),
            old_string="Why\u2019s",
            new_string="Because",
        )
        self.assertEqual(code, 2)
        self.assertIn("could not verify", err)


class SkillHookCommandTests(unittest.TestCase):
    def test_hook_commands_run_scripts_from_plugin_root(self):
        skill = SCRIPTS.parent / "SKILL.md"
        commands = re.findall(r"command: '(.+)'", skill.read_text().split("\n---\n")[0])
        self.assertEqual(len(commands), 2)
        plugin_root = str(SCRIPTS.parents[2])
        with tempfile.TemporaryDirectory() as home:
            for command in commands:
                result = subprocess.run(
                    ["bash", "-c", command],
                    env={
                        "HOME": home,
                        "PATH": "/usr/bin:/bin",
                        "CLAUDE_PLUGIN_ROOT": plugin_root,
                    },
                    input="{}",
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, command + result.stderr)
                self.assertNotIn("No such file", result.stderr)


if __name__ == "__main__":
    unittest.main()
