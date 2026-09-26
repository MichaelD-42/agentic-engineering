import json
import os
import subprocess
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
        self.assertIsNone(
            sc.problems(
                [superpowers(self.healthy, marketplace="superpowers-marketplace")]
            )
        )

    def test_missing_warns_both(self):
        self.assertEqual(sc.problems([]), (sc.MISSING_USER, sc.MISSING_MODEL))

    def test_disabled_warns_both(self):
        self.assertEqual(
            sc.problems([superpowers(self.healthy, enabled=False)]),
            (sc.MISSING_USER, sc.MISSING_MODEL),
        )

    def test_missing_companion_warns_user_only(self):
        self.assertEqual(
            sc.problems([superpowers(self.broken)]), (sc.NO_COMPANION_USER, None)
        )

    def test_empty_install_path_is_missing_companion(self):
        entry = superpowers(self.healthy)
        entry["installPath"] = ""
        self.assertEqual(sc.problems([entry]), (sc.NO_COMPANION_USER, None))

    def test_one_disabled_one_healthy_is_none(self):
        self.assertIsNone(
            sc.problems(
                [superpowers(self.broken, enabled=False), superpowers(self.healthy)]
            )
        )

    def test_non_dict_entries_ignored(self):
        self.assertIsNone(sc.problems(["junk", 3, superpowers(self.healthy)]))


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
        # A Python fake: PATH holds only self.bin, so a shell fake can't find cat.
        script.write_text(
            f"#!{sys.executable}\nimport sys\n"
            f"sys.stdout.write(open({str(out)!r}).read())\nsys.exit({code})\n"
        )
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
