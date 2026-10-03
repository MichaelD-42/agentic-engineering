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
        self.stdout = result.stdout
        return result.returncode, result.stderr

    def setUp(self):
        super().setUp()
        self.accepted = self.write("docs/adr/0001-a.md", madr("A"))
        self.proposed = self.write("docs/adr/0002-b.md", madr("B", status="proposed"))
        adr.write_index(self.root / "docs/adr")


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

    def test_readme_edit_restores_the_index(self):
        readme = self.root / "docs/adr/README.md"
        readme.write_text("# Decisions\n")
        code, err = self.hook("hook_validate.py", "Write", file_path=str(readme))
        self.assertEqual((code, err), (0, ""))
        self.assertIn("adr-index:start", readme.read_text())

    def test_adr_write_refreshes_a_stale_index(self):
        new = self.write("docs/adr/0003-c.md", madr("C", status="proposed"))
        code, err = self.hook("hook_validate.py", "Write", file_path=str(new))
        self.assertEqual((code, err), (0, ""))
        self.assertIn("0003-c.md", (self.root / "docs/adr/README.md").read_text())

    def test_wording_fix_to_accepted_adr_is_allowed(self):
        self.accepted.write_text(self.accepted.read_text().replace("Why.", "Why, clearly."))
        code, err = self.hook("hook_validate.py", "Edit", file_path=str(self.accepted))
        self.assertEqual((code, err), (0, ""))

    def test_long_proposal_warns_without_blocking(self):
        self.proposed.write_text(
            madr("B", status="proposed", body="\n".join(f"line {i}" for i in range(70)))
        )
        code, err = self.hook("hook_validate.py", "Write", file_path=str(self.proposed))
        self.assertEqual((code, err), (0, ""))
        context = json.loads(self.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("exceeds cap of 60", context)

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

    def test_validate_reports_when_cwd_is_elsewhere(self):
        self.proposed.write_text(madr("B", status="maybe"))
        adr.write_index(self.root / "docs/adr")
        code, _ = self.hook_from(
            "/", "hook_validate.py", "Write", file_path=str(self.proposed)
        )
        self.assertEqual(code, 2)


class SkillHookCommandTests(unittest.TestCase):
    def test_hook_commands_run_scripts_from_plugin_root(self):
        skill = SCRIPTS.parent / "SKILL.md"
        commands = re.findall(r"command: '(.+)'", skill.read_text().split("\n---\n")[0])
        self.assertEqual(len(commands), 1)
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
