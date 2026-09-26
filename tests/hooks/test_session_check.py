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
        self.assertIsNone(sc.problems([superpowers(self.healthy, marketplace="superpowers-marketplace")]))

    def test_missing_warns_both(self):
        self.assertEqual(sc.problems([]), (sc.MISSING_USER, sc.MISSING_MODEL))

    def test_disabled_warns_both(self):
        self.assertEqual(
            sc.problems([superpowers(self.healthy, enabled=False)]),
            (sc.MISSING_USER, sc.MISSING_MODEL),
        )

    def test_missing_companion_warns_user_only(self):
        self.assertEqual(sc.problems([superpowers(self.broken)]), (sc.NO_COMPANION_USER, None))

    def test_empty_install_path_is_missing_companion(self):
        entry = superpowers(self.healthy)
        entry["installPath"] = ""
        self.assertEqual(sc.problems([entry]), (sc.NO_COMPANION_USER, None))

    def test_one_disabled_one_healthy_is_none(self):
        self.assertIsNone(
            sc.problems([superpowers(self.broken, enabled=False), superpowers(self.healthy)])
        )

    def test_non_dict_entries_ignored(self):
        self.assertIsNone(sc.problems(["junk", 3, superpowers(self.healthy)]))
