"""Tests for skill runbook merge and discover allowlist."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "maestro" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from runbooks import (  # noqa: E402
    attach_runbooks,
    is_repo_allowlisted,
    load_discover_allowlist,
    load_runbooks,
    resolve_preflight_command,
)


class TestRunbooks(unittest.TestCase):
    def test_bundled_has_ui_ux_pro_max(self) -> None:
        data = load_runbooks()
        skills = data["skills"]
        self.assertIn("ui-ux-pro-max", skills)
        self.assertTrue(skills["ui-ux-pro-max"].get("preflight"))

    def test_user_override_merge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            maestro_home = home / ".maestro"
            maestro_home.mkdir()
            user_file = maestro_home / "skill-runbooks.user.json"
            user_file.write_text(
                json.dumps(
                    {
                        "skills": {
                            "my-skill": {
                                "summary": "custom",
                                "preflight": [],
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            # Patch MAESTRO_HOME for this test
            import runbooks as rb  # noqa: E402

            original = rb.MAESTRO_HOME
            rb.MAESTRO_HOME = maestro_home
            rb.USER_RUNBOOKS = maestro_home / "skill-runbooks.user.json"
            try:
                data = load_runbooks()
                self.assertIn("my-skill", data["skills"])
                self.assertIn("ui-ux-pro-max", data["skills"])
            finally:
                rb.MAESTRO_HOME = original
                rb.USER_RUNBOOKS = original / "skill-runbooks.user.json"

    def test_attach_runbooks_resolves_placeholders(self) -> None:
        results = [
            {
                "name": "ui-ux-pro-max",
                "folder": "ui-ux-pro-max",
                "path": "/tmp/skills/ui-ux-pro-max/SKILL.md",
            }
        ]
        runbooks = load_runbooks()
        attach_runbooks(results, runbooks, query="dashboard", project_name="Demo")
        rb = results[0]["runbook"]
        pf = rb["preflight"][0]
        self.assertIn("resolved_args", pf)
        self.assertIn("dashboard", pf["resolved_args"])

    def test_resolve_preflight_command(self) -> None:
        args = resolve_preflight_command(
            {
                "args": ["{skill_scripts}/search.py", "{query}", "-p", "{project_name}"],
            },
            skill_path="/skills/foo/SKILL.md",
            query="landing page",
            project_name="Acme",
        )
        self.assertTrue(str(args[0]).endswith("search.py"))
        self.assertEqual(args[1], "landing page")
        self.assertEqual(args[3], "Acme")

    def test_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            import runbooks as rb  # noqa: E402

            path = Path(tmp) / "discover-allowlist.txt"
            path.write_text("# comment\nrodovalhofs/maestro\n", encoding="utf-8")
            original = rb.DISCOVER_ALLOWLIST
            rb.DISCOVER_ALLOWLIST = path
            try:
                items = load_discover_allowlist()
                self.assertEqual(items, ["rodovalhofs/maestro"])
                self.assertTrue(is_repo_allowlisted("rodovalhofs/maestro"))
                self.assertFalse(is_repo_allowlisted("evil/unknown"))
            finally:
                rb.DISCOVER_ALLOWLIST = original


if __name__ == "__main__":
    unittest.main()
